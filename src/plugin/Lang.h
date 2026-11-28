// SkyrimYacht - a dice game for Skyrim Special Edition.
// Copyright (C) 2026 evodube. GPL-3.0 (LICENSE.txt).
#pragma once

// Every word the table shows, by key: English is built in, and a translation file replaces any of it.
//   Data\Interface\Translations\SkyrimYacht_<LANGUAGE>.txt   ($KEY<tab>text per line, UTF-16 or UTF-8)
// The language is the game's own (sLanguage) unless SkyrimYacht.ini names one. A line the file doesn't have stays
// English, so a half-done translation still works. Placeholders are {0}, {1}... and may go in any order.
namespace Lang
{
	void        Load();
	std::string Language();     // e.g. ENGLISH, RUSSIAN
	std::string FontFile(int a_which);  // the translation's own font for 0 the plain text, 1 the book text ("" = ours)

	// The text for a key (or the English given, if the translation hasn't got it). The pointer stays good.
	const char* T(std::string_view a_key, const char* a_english);

	// The same, with {0} {1}... filled in. A translation whose placeholders don't fit falls back to the English.
	template <class... Args>
	std::string F(std::string_view a_key, const char* a_english, Args&&... a_args)
	{
		const char* t = T(a_key, a_english);
		try {
			return fmt::format(fmt::runtime(t), a_args...);
		} catch (...) {
			try {
				return fmt::format(fmt::runtime(a_english), a_args...);
			} catch (...) {
				return a_english;
			}
		}
	}

	// Every character the translation uses (to put in the fonts up front).
	const std::vector<std::uint32_t>& UsedCodepoints();
}
