// SkyrimYacht - a dice game for Skyrim Special Edition.
// Copyright (C) 2026 evodube. GPL-3.0 (LICENSE.txt).
#include "Lang.h"
#include "Config.h"

namespace Lang
{
	namespace
	{
		std::string                                     g_lang = "ENGLISH";
		std::unordered_map<std::string, std::string>    g_text;      // key -> translated text (UTF-8)
		std::unordered_map<std::string, std::string>    g_keyShown;  // ShowKeys: the key itself, kept alive
		std::vector<std::uint32_t>                      g_used;
		std::mutex                                      g_mtx;

		std::string ToUtf8(const std::u16string& a_s)
		{
			std::string out;
			for (std::size_t i = 0; i < a_s.size(); ++i) {
				std::uint32_t c = a_s[i];
				if (c >= 0xD800 && c <= 0xDBFF && i + 1 < a_s.size() && a_s[i + 1] >= 0xDC00 && a_s[i + 1] <= 0xDFFF) {
					c = 0x10000 + ((c - 0xD800) << 10) + (a_s[i + 1] - 0xDC00);
					++i;
				}
				if (c < 0x80) {
					out += static_cast<char>(c);
				} else if (c < 0x800) {
					out += static_cast<char>(0xC0 | (c >> 6));
					out += static_cast<char>(0x80 | (c & 0x3F));
				} else if (c < 0x10000) {
					out += static_cast<char>(0xE0 | (c >> 12));
					out += static_cast<char>(0x80 | ((c >> 6) & 0x3F));
					out += static_cast<char>(0x80 | (c & 0x3F));
				} else {
					out += static_cast<char>(0xF0 | (c >> 18));
					out += static_cast<char>(0x80 | ((c >> 12) & 0x3F));
					out += static_cast<char>(0x80 | ((c >> 6) & 0x3F));
					out += static_cast<char>(0x80 | (c & 0x3F));
				}
			}
			return out;
		}

		// The file as UTF-8, whichever way it was saved (UTF-16 LE/BE with a BOM, as the game's own; or UTF-8)
		std::string ReadText(const std::filesystem::path& a_path)
		{
			std::ifstream f(a_path, std::ios::binary);
			std::string   raw((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
			if (raw.size() >= 2 && (static_cast<unsigned char>(raw[0]) == 0xFF && static_cast<unsigned char>(raw[1]) == 0xFE ||
									   static_cast<unsigned char>(raw[0]) == 0xFE && static_cast<unsigned char>(raw[1]) == 0xFF)) {
				const bool     le = static_cast<unsigned char>(raw[0]) == 0xFF;
				std::u16string w;
				for (std::size_t i = 2; i + 1 < raw.size(); i += 2) {
					const auto a = static_cast<unsigned char>(raw[i]), b = static_cast<unsigned char>(raw[i + 1]);
					w += static_cast<char16_t>(le ? (a | (b << 8)) : ((a << 8) | b));
				}
				return ToUtf8(w);
			}
			if (raw.size() >= 3 && static_cast<unsigned char>(raw[0]) == 0xEF && static_cast<unsigned char>(raw[1]) == 0xBB &&
				static_cast<unsigned char>(raw[2]) == 0xBF) {
				raw.erase(0, 3);
			}
			return raw;
		}

		void NoteUsed(const std::string& a_s)
		{
			const auto* p = reinterpret_cast<const unsigned char*>(a_s.data());
			const auto* e = p + a_s.size();
			while (p < e) {
				std::uint32_t c = *p;
				int           n = c < 0x80 ? 0 : c < 0xE0 ? 1 : c < 0xF0 ? 2 : 3;
				c = n == 0 ? c : n == 1 ? (c & 0x1F) : n == 2 ? (c & 0x0F) : (c & 0x07);
				++p;
				for (; n > 0 && p < e; --n, ++p) {
					c = (c << 6) | (*p & 0x3F);
				}
				if (c >= 0x80) {
					g_used.push_back(c);
				}
			}
		}

		std::string GameLanguage()
		{
			if (auto* ini = RE::INISettingCollection::GetSingleton()) {
				if (auto* s = ini->GetSetting("sLanguage:General"); s && s->GetType() == RE::Setting::Type::kString && s->GetString()) {
					return s->GetString();
				}
			}
			return "ENGLISH";
		}
	}

	void Load()
	{
		std::lock_guard lk(g_mtx);
		g_text.clear();
		g_used.clear();
		g_lang = Config::Get().language.empty() ? GameLanguage() : Config::Get().language;
		std::transform(g_lang.begin(), g_lang.end(), g_lang.begin(), [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
		const std::filesystem::path path = "Data\\Interface\\Translations\\SkyrimYacht_" + g_lang + ".txt";
		std::error_code             ec;
		if (!std::filesystem::exists(path, ec)) {
			spdlog::info("Language {}: no {} (English it is)", g_lang, path.string());
			return;
		}
		const std::string text = ReadText(path);
		std::size_t       lines = 0, start = 0;
		while (start < text.size()) {
			std::size_t end = text.find('\n', start);
			if (end == std::string::npos) {
				end = text.size();
			}
			std::string line = text.substr(start, end - start);
			start = end + 1;
			if (!line.empty() && line.back() == '\r') {
				line.pop_back();
			}
			if (line.empty() || line[0] != '$') {
				continue;  // blank lines and comments
			}
			const auto tab = line.find('\t');
			if (tab == std::string::npos) {
				continue;
			}
			std::string key = line.substr(0, tab), val = line.substr(tab + 1);
			// "\n" in the file is a line break
			for (std::size_t p = val.find("\\n"); p != std::string::npos; p = val.find("\\n", p + 1)) {
				val.replace(p, 2, "\n");
			}
			if (!val.empty()) {
				NoteUsed(val);
				g_text[std::move(key)] = std::move(val);
				++lines;
			}
		}
		std::sort(g_used.begin(), g_used.end());
		g_used.erase(std::unique(g_used.begin(), g_used.end()), g_used.end());
		spdlog::info("Language {}: {} lines from {} ({} distinct non-ASCII characters)", g_lang, lines, path.string(), g_used.size());
	}

	std::string Language() { return g_lang; }

	std::string FontFile(int a_which)
	{
		std::lock_guard lk(g_mtx);
		const auto      it = g_text.find(a_which == 0 ? "$YA__FontText" : "$YA__FontBook");
		return it == g_text.end() ? std::string() : it->second;
	}

	const char* T(std::string_view a_key, const char* a_english)
	{
		std::lock_guard lk(g_mtx);
		const std::string key(a_key);
		if (Config::Get().showKeys) {
			auto [it, _] = g_keyShown.try_emplace(key, key);
			return it->second.c_str();
		}
		const auto it = g_text.find(key);
		return it == g_text.end() ? a_english : it->second.c_str();
	}

	const std::vector<std::uint32_t>& UsedCodepoints() { return g_used; }
}
