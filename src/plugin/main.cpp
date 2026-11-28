// SkyrimYacht - a dice game for Skyrim Special Edition.
// Copyright (C) 2026 evodube
//
// This program is free software: you can redistribute it and/or modify it under the terms of the
// GNU General Public License as published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
// even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License along with this program (LICENSE.txt).
// If not, see <https://www.gnu.org/licenses/>.

#include "Menu.h"
#include "Config.h"
#include "Game.h"
#include "Overlay.h"

// One DLL for every version: CommonLibSSE-NG built for SE and AE, every game address taken from Address Library by
// ID, and the plugin declared version-independent (add_commonlibsse_plugin ... USE_ADDRESS_LIBRARY), so it loads on
// 1.5.97, every 1.6 release (1.6.1170 included) and later ones Address Library covers, Steam and GOG.
namespace
{
	void SetupLog()
	{
		auto path = SKSE::log::log_directory();
		if (!path) {
			return;
		}
		*path /= "SkyrimYacht.log";
		auto sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(path->string(), true);
		auto log = std::make_shared<spdlog::logger>("global log", std::move(sink));
		log->set_level(spdlog::level::info);
		log->flush_on(spdlog::level::info);
		spdlog::set_default_logger(std::move(log));
		spdlog::set_pattern("[%H:%M:%S.%e] [%l] %v");
	}

	void LogEnvironment()
	{
		const auto ver = REL::Module::get().version();
		spdlog::info("Game version {} ({})", ver.string("."sv), REL::Module::IsAE() ? "AE" : (REL::Module::IsSE() ? "SE" : "other"));
		const auto lib = REL::Module::IsAE() ? fmt::format("Data\\SKSE\\Plugins\\versionlib-{}.bin", ver.string()) :
		                                       fmt::format("Data\\SKSE\\Plugins\\version-{}.bin", ver.string());
		std::error_code ec;
		if (std::filesystem::exists(lib, ec)) {
			spdlog::info("Address Library found: {}", lib);
		} else {
			spdlog::critical("Address Library NOT FOUND: {} - install 'Address Library for SKSE Plugins' for this game version", lib);
		}
	}

	// ------------------------------------------------------------------ Present hook (and Present1)
	// Each swap chain type (vtable) is hooked ONCE, and what its Present slot held then is kept for good as the next in
	// line. Other overlays (HUD widgets, UI frameworks) hook the same slot after us and call us in turn: hooking that
	// slot again would take their chain, which ends in us, as our next in line, and Present would go round in a loop
	// until the stack ran out. So a vtable already hooked is never hooked again, whatever is in its slot now.
	using PresentFn = HRESULT(STDMETHODCALLTYPE*)(IDXGISwapChain*, UINT, UINT);
	using Present1Fn = HRESULT(STDMETHODCALLTYPE*)(IDXGISwapChain1*, UINT, UINT, const DXGI_PRESENT_PARAMETERS*);
	std::atomic<bool>          g_presentDisabled{ false };
	std::atomic<bool>          g_tickDisabled{ false };
	std::atomic<bool>          g_tickQueued{ false };
	std::atomic<std::uint64_t> g_presents{ 0 };
	thread_local int           t_inPresent = 0;  // Present1 may call Present (or the other way round): once a frame
	constexpr int              kMaxDepth = 6;     // deeper than this, Present has come back round to us in a loop
	std::atomic<bool>          g_loopSaid{ false };

	// vtable -> the original (next in line) for that vtable; written once each (main thread), read from Present
	constexpr int                           kTypes = 4;
	std::array<std::atomic<void**>, kTypes> g_vt{}, g_vt1{};
	std::array<std::atomic<void*>, kTypes>  g_orig{}, g_orig1{};

	void* OriginalFor(const std::array<std::atomic<void**>, kTypes>& a_vts, const std::array<std::atomic<void*>, kTypes>& a_origs, void* a_obj)
	{
		auto** vt = *reinterpret_cast<void***>(a_obj);
		for (int i = 0; i < kTypes; ++i) {
			if (a_vts[i].load(std::memory_order_acquire) == vt) {
				return a_origs[i].load(std::memory_order_acquire);
			}
		}
		// (an object of a type not hooked by us, reaching us through another mod: the first type's next in line)
		return a_origs[0].load(std::memory_order_acquire);
	}

	void SafeTick()
	{
		__try {
			Game::FrameTick();
		} __except (Overlay::SehFilter(GetExceptionInformation(), "FrameTick")) {
			g_tickDisabled = true;
		}
	}

	void SafeOnPresent(IDXGISwapChain* a_sc)
	{
		__try {
			Overlay::OnPresent(a_sc);
		} __except (Overlay::SehFilter(GetExceptionInformation(), "OnPresent")) {
			g_presentDisabled = true;
		}
	}

	void OnFrame(IDXGISwapChain* a_sc)
	{
		++g_presents;
		if (!g_tickDisabled && !g_tickQueued.exchange(true)) {
			SKSE::GetTaskInterface()->AddTask([] {
				g_tickQueued = false;
				if (!g_tickDisabled) {
					SafeTick();
				}
			});
		}
		if (!g_presentDisabled) {
			SafeOnPresent(a_sc);
		}
	}

	// Present came back to us more than kMaxDepth deep: the hooks of several mods are calling each other in a circle.
	// The circle is broken here (this frame isn't shown) rather than run until the stack overflows.
	bool LoopedBack()
	{
		if (t_inPresent <= kMaxDepth) {
			return false;
		}
		if (!g_loopSaid.exchange(true)) {
			spdlog::error("Present hooks are calling each other in a loop (another overlay mod hooked Present again after us): breaking it");
		}
		return true;
	}

	HRESULT STDMETHODCALLTYPE HookedPresent(IDXGISwapChain* a_sc, UINT a_sync, UINT a_flags)
	{
		if (t_inPresent++ == 0) {
			OnFrame(a_sc);
		}
		HRESULT hr = S_OK;
		if (!LoopedBack()) {
			auto next = reinterpret_cast<PresentFn>(OriginalFor(g_vt, g_orig, a_sc));
			hr = next ? next(a_sc, a_sync, a_flags) : S_OK;
		}
		--t_inPresent;
		return hr;
	}

	HRESULT STDMETHODCALLTYPE HookedPresent1(IDXGISwapChain1* a_sc, UINT a_sync, UINT a_flags, const DXGI_PRESENT_PARAMETERS* a_params)
	{
		if (t_inPresent++ == 0) {
			OnFrame(a_sc);
		}
		HRESULT hr = S_OK;
		if (!LoopedBack()) {
			auto next = reinterpret_cast<Present1Fn>(OriginalFor(g_vt1, g_orig1, a_sc));
			hr = next ? next(a_sc, a_sync, a_flags, a_params) : S_OK;
		}
		--t_inPresent;
		return hr;
	}

	bool Hooked(const std::array<std::atomic<void**>, kTypes>& a_vts, void** a_vt)
	{
		for (const auto& v : a_vts) {
			if (v.load() == a_vt) {
				return true;
			}
		}
		return false;
	}

	// One vtable's slot hooked, its next in line kept for good (never a vtable already hooked: see above)
	bool PatchSlot(std::array<std::atomic<void**>, kTypes>& a_vts, std::array<std::atomic<void*>, kTypes>& a_origs, void** a_vtable, int a_slot, void* a_hook)
	{
		if (Hooked(a_vts, a_vtable)) {
			return true;
		}
		if (a_vtable[a_slot] == a_hook) {
			return false;  // (our hook copied into a vtable we didn't hook: no original to keep, left alone)
		}
		int free = -1;
		for (int i = 0; i < kTypes; ++i) {
			if (!a_vts[i].load()) {
				free = i;
				break;
			}
		}
		if (free < 0) {
			spdlog::warn("Present: too many swap chain types, not hooking another");
			return false;
		}
		DWORD old = 0;
		if (!::VirtualProtect(&a_vtable[a_slot], sizeof(void*), PAGE_EXECUTE_READWRITE, &old)) {
			spdlog::error("VirtualProtect failed ({})", ::GetLastError());
			return false;
		}
		a_origs[free].store(a_vtable[a_slot], std::memory_order_release);
		a_vts[free].store(a_vtable, std::memory_order_release);
		a_vtable[a_slot] = a_hook;
		::VirtualProtect(&a_vtable[a_slot], sizeof(void*), old, &old);
		return true;
	}

	bool PatchPresentSlot(IDXGISwapChain* a_sc)
	{
		auto** vtable = *reinterpret_cast<void***>(a_sc);
		if (!PatchSlot(g_vt, g_orig, vtable, 8, reinterpret_cast<void*>(&HookedPresent))) {
			return false;
		}
		IDXGISwapChain1* sc1 = nullptr;
		if (SUCCEEDED(a_sc->QueryInterface(__uuidof(IDXGISwapChain1), reinterpret_cast<void**>(&sc1))) && sc1) {
			PatchSlot(g_vt1, g_orig1, *reinterpret_cast<void***>(sc1), 22, reinterpret_cast<void*>(&HookedPresent1));
			sc1->Release();
		}
		return true;
	}

	// The game's swap chain (whatever a graphics mod has put there: ENB's, ReShade's, a frame generator's), checked
	// to really be one before anything is done with it
	IDXGISwapChain* GameSwapChain()
	{
		__try {
			auto* renderer = RE::BSGraphics::Renderer::GetSingleton();
			auto* sc = renderer ? reinterpret_cast<IDXGISwapChain*>(renderer->GetRuntimeData().renderWindows[0].swapChain) : nullptr;
			if (!sc) {
				return nullptr;
			}
			IDXGISwapChain* probe = nullptr;
			if (FAILED(sc->QueryInterface(__uuidof(IDXGISwapChain), reinterpret_cast<void**>(&probe))) || !probe) {
				return nullptr;
			}
			probe->Release();
			return sc;
		} __except (Overlay::SehFilter(GetExceptionInformation(), "GameSwapChain")) {
			return nullptr;
		}
	}

	bool SafeInstallPresentHook()
	{
		__try {
			auto* sc = GameSwapChain();
			return sc && PatchPresentSlot(sc);
		} __except (Overlay::SehFilter(GetExceptionInformation(), "InstallPresentHook")) {
			return false;
		}
	}

	// another mod may put a swap chain of its own in later (frame generation, upscalers): if frames stop coming through
	// the hook and the game's swap chain is of a type not hooked yet, that type is hooked. (A type already hooked never
	// is again, even if other mods have hooked it since.)
	void WatchSwapChain()
	{
		std::thread([] {
			int tries = 0;
			for (std::uint64_t last = g_presents; tries < 20;) {
				std::this_thread::sleep_for(std::chrono::seconds(3));
				const std::uint64_t now = g_presents;
				if (now != last) {
					last = now;
					continue;
				}
				++tries;
				SKSE::GetTaskInterface()->AddTask([] {
					auto* sc = GameSwapChain();
					if (sc && !Hooked(g_vt, *reinterpret_cast<void***>(sc))) {
						spdlog::info("No frames through the Present hook, and the game's swap chain is a new one: hooking it");
						PatchPresentSlot(sc);
					}
				});
			}
		}).detach();
	}

	void OnMessage(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kPostLoad:
			Menu::Register();
			break;
		case SKSE::MessagingInterface::kDataLoaded:
			Game::OnDataLoaded();
			if (SafeInstallPresentHook()) {
				spdlog::info("Present hook installed");
				WatchSwapChain();
			} else {
				spdlog::error("Could not install the Present hook - the game's interface will not appear");
			}
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			{
				static bool s_input = false;
				if (!s_input) {
					s_input = true;
					if (!Overlay::InstallInputSink()) {
						spdlog::error("Could not register for input events");
					}
				}
			}
			Game::OnGameLoaded();
			break;
		default:
			break;
		}
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SetupLog();
	spdlog::info("SkyrimYacht {} loaded", SKSE::PluginDeclaration::GetSingleton()->GetVersion().string("."sv));
	LogEnvironment();
	SKSE::AllocTrampoline(64);
	Config::Load();
	if (auto* ser = SKSE::GetSerializationInterface()) {
		ser->SetUniqueID('YCHT');
		ser->SetSaveCallback(Game::Save);
		ser->SetLoadCallback(Game::Load);
		ser->SetRevertCallback(Game::Revert);
	}
	if (!SKSE::GetMessagingInterface()->RegisterListener(OnMessage)) {
		spdlog::error("Could not register with the SKSE messaging interface");
		return false;
	}
	return true;
}
