#!/usr/bin/env python3
# SkyrimYacht - builds the translation files from the source.
#   assets/translations/SkyrimYacht_ENGLISH.txt  every line the DLL shows, as it is in the code (the template)
#   assets/translations/SkyrimYacht_RUSSIAN.txt  / _CHINESE.txt  the bundled translations (drafts for native speakers)
#   assets/translations/Translating.txt          the guide for translators, with where each line shows
# The files are UTF-16 LE with a BOM and CRLF, the game's own format ($KEY<tab>text), so xTranslator opens them.
# Run it after changing any text in src/plugin/Game.cpp: a key the code has and a translation lacks shows in English.
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "translations")


def english():
    src = open(os.path.join(ROOT, "src", "plugin", "Game.cpp"), encoding="utf-8").read()
    keys = {}
    for m in re.finditer(r'(?:\bL|Lang::F)\("(\$YA_\w+)",\s*"((?:[^"\\]|\\.)*)"', src):
        keys.setdefault(m.group(1), m.group(2).replace('\\"', '"'))
    # the cups, the dice sets and their blurbs, and the score boxes, by their ids
    cups = re.search(r"constexpr CupInfo kCups\[\] = \{(.*?)\n\t\t\};", src, re.S).group(1)
    for m in re.finditer(r'\{ "(\w+)", "([^"]+)"', cups):
        keys["$YA_Cup_" + m.group(1)] = m.group(2)
    dice = re.search(r"constexpr DiceInfo kDiceInfo\[15\] = \{(.*?)\n\t\t\};", src, re.S).group(1)
    for m in re.finditer(r'\{ "(\w+)", \d+, \d+, "([^"]+)" \}', dice):
        keys["$YA_Dice" + m.group(1)] = m.group(1)
        keys["$YA_Dice" + m.group(1) + "Text"] = m.group(2)
    ysrc = open(os.path.join(ROOT, "src", "sim", "Yacht.cpp"), encoding="utf-8").read()
    names = re.findall(r'"([^"]+)"', re.search(r"names\[kCategories\] = \{(.*?)\};", ysrc, re.S).group(1))
    cats = ["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes", "ThreeKind", "FourKind", "FullHouse", "SmallStraight",
            "LargeStraight", "Yacht", "Chance"]
    for c, n in zip(cats, names):
        keys["$YA_Cat" + c] = n
    return keys


# Where each line shows (for Translating.txt)
WHERE = {
    "Toast": "a message across the middle of the table", "Payout": "the result screen, under the score",
    "Hint": "the help line along the bottom while you play", "Card": "the score cards", "Key": "the key bar, bottom right",
    "Sound": "the sound panel", "Help": "the How to play box", "Label": "the cup and dice labels",
    "Forfeit": "the forfeit box", "Wager": "the wager screen", "Purse": "the wager screen", "Shop": "the innkeeper's dice shop",
    "Over": "the result screen", "Cup_": "a cup's name", "Dice": "a dice set's name, or with Text its description",
    "Cat": "a score box on the card",
}

RU = {
    "$YA_OffTableToast": "Мимо стола! Бросайте снова",
    "$YA_PayoutWin": "Вы забираете {0} септимов",
    "$YA_NowSelling": "Трактирщики теперь продают кости: {0}",
    "$YA_PayoutDraw": "Ваши {0} септимов возвращаются к вам",
    "$YA_PayoutLose": "{0} забирает ваши {1} септимов",
    "$YA_OppScores": "{0}: {1} — {2}",
    "$YA_Scratched": "Вычеркнуто",
    "$YA_NoRollsToast": "Бросков больше нет",
    "$YA_BoardClear": "Стол уже пуст",
    "$YA_DiceFirst": "Сначала положите кости в стакан или на подставку",
    "$YA_CupEmpty": "Стакан пуст",
    "$YA_NoGold": "У вас нет столько золота",
    "$YA_CantAfford": "Вам это не по карману",
    "$YA_BoughtToast": "Кости «{0}» теперь ваши",
    "$YA_YourOpponent": "Ваш соперник",
    "$YA_TurnOver": "Игра окончена",
    "$YA_YourTurn": "Ваш ход",
    "$YA_WagerTop": "Ставка: {0} септимов",
    "$YA_HintOpp": "Ходит {0}",
    "$YA_HintReady": "Зажмите левую кнопку и ведите мышь, чтобы трясти стакан. Отпустите, чтобы бросить.",
    "$YA_HintShake": "Потрясите и отпустите: стакан наклонится туда, куда вы двигали его в последний раз.",
    "$YA_HintRolling": "Кости катятся",
    "$YA_HintRedo": "Мимо стола. Бросайте снова.",
    "$YA_HintChoose": "Нажмите на кость, чтобы оставить её. Перетащите кости в стакан, чтобы перебросить, или выберите клетку на карточке.",
    "$YA_HintNoRolls": "Бросков больше нет. Выберите клетку на карточке.",
    "$YA_CardYours": "Ваша",
    "$YA_Record": "Счёт {0}-{1}{2}",
    "$YA_Drawn": ", ничьих: {0}",
    "$YA_CardUpper": "Верх",
    "$YA_CardLower": "Низ",
    "$YA_CardBonus": "Бонус 35 за 63",
    "$YA_CardYachtBonus": "Бонусы за яхту",
    "$YA_KeyShout": "Фус Ро Да",
    "$YA_KeyHelp": "Как играть",
    "$YA_KeyMuted": "Без звука",
    "$YA_KeySound": "Звук",
    "$YA_KeyForfeit": "Сдаться",
    "$YA_SoundTitle": "Звук",
    "$YA_SoundMusic": "Музыка",
    "$YA_SoundDice": "Кости и стаканы",
    "$YA_SoundEffects": "Эффекты",
    "$YA_SoundUnmute": "Включить звук",
    "$YA_SoundMuteAll": "Выключить всё",
    "$YA_HelpTitle": "Яхта",
    "$YA_Help1": "Зажмите левую кнопку и ведите мышь, чтобы поднять стакан и потрясти его. Отпустите, и кости вылетят туда, куда вы двигали его в последний раз. Если кость улетела со стола, бросайте снова.",
    "$YA_Help2": "Нажмите на кость, чтобы поставить её на подставку. Перетащите её обратно в стакан, чтобы перебросить. Стакан ждёт, пока стол не опустеет.",
    "$YA_Help3": "Любой стакан, который у вас с собой, может стать вашим за столом. Каждые десять побед трактирщики продают вам набор костей получше.",
    "$YA_LabelCup": "СТАКАН",
    "$YA_LabelDice": "КОСТИ",
    "$YA_ForfeitAsk": "Сдаться?",
    "$YA_ForfeitNote": "Это засчитается как поражение. {0} забирает ваши {1} септимов",
    "$YA_KeepPlaying": "Играть дальше",
    "$YA_WagerWith": "Партия в яхту с соперником: {0}",
    "$YA_WagerNote": "Ставка в септимах. Выиграете — получите {0}",
    "$YA_Purse": "В кошельке: {0} септимов",
    "$YA_PlaceBet": "Сделать ставку",
    "$YA_Leave": "Уйти",
    "$YA_ShopStock": "Товар: {0}",
    "$YA_ShopTitle": "Кости",
    "$YA_ShopPurse": "В кошельке: {0} септимов  -  побед: {1}",
    "$YA_ShopInUse": "В игре",
    "$YA_ShopOwned": "Есть",
    "$YA_ShopPrice": "{0} септимов",
    "$YA_ShopWins": "Побед: {0}",
    "$YA_ShopStarting": "Начальные кости",
    "$YA_ShopStats": "Цена  {0}     Побед  {1}",
    "$YA_ShopUse": "Играть ими",
    "$YA_ShopBuy": "Купить  {0}",
    "$YA_ShopNoGold": "Не хватает золота",
    "$YA_ShopAfter": "В продаже после {0} побед",
    "$YA_ShopYours": "Ваши игральные кости",
    "$YA_ShopDone": "Готово",
    "$YA_OverWin": "Победа",
    "$YA_OverDraw": "Ничья",
    "$YA_OverForfeit": "Вы сдались",
    "$YA_OverLose": "Поражение",
    "$YA_OverTitle": "Игра окончена",
    "$YA_OverRecord": "Ваш счёт против соперника ({0}): {1}-{2}{3}",
    "$YA_OverCup": "Ваш стакан: {0}",
    "$YA_Rematch": "Реванш",
    "$YA_BoughtHud": "Кости «{0}» теперь ваши. Вы сыграете ими за следующим столом.",
    "$YA_Innkeeper": "Трактирщик",
    "$YA_Leaving": "Вы уходите из-за стола",
    "$YA_SettingUp": "Готовим стол",
    "$YA_Cup_tankard": "Кружка",
    "$YA_Cup_bloodtankard": "Кровавая кружка",
    "$YA_Cup_glazedcup": "Глазурованная чашка",
    "$YA_Cup_goblet": "Глазурованный кубок",
    "$YA_Cup_dwemer": "Двемерская чашка",
    "$YA_Cup_dwemer2": "Узорная двемерская чашка",
    "$YA_Cup_silver": "Серебряный кубок",
    "$YA_Cup_silver2": "Серебряная чаша",
    "$YA_DiceBone": "Костяные", "$YA_DiceBoneText": "Резная кость. Пожелтевшая, исцарапанная, с грязью в точках.",
    "$YA_DiceIron": "Железные", "$YA_DiceIronText": "Кованое железо в ямках и пятнах ржавчины, с выбитыми точками.",
    "$YA_DiceSteel": "Стальные", "$YA_DiceSteelText": "Шлифованная сталь с чётко выгравированными точками.",
    "$YA_DiceCorundum": "Корундовые", "$YA_DiceCorundumText": "Медно-рыжий корунд, слегка позеленевший по краям.",
    "$YA_DiceDwemer": "Двемерские", "$YA_DiceDwemerText": "Двемерская бронза, точки в виде шестерёнок, позеленевшая от времени.",
    "$YA_DiceOrichalcum": "Орихалковые", "$YA_DiceOrichalcumText": "Орихалк орочьей ковки, тёмная зелёная бронза в следах когтей.",
    "$YA_DiceSilver": "Серебряные", "$YA_DiceSilverText": "Полированное серебро, потемневшее по углам, с чернёными точками.",
    "$YA_DiceQuicksilver": "Ртутные", "$YA_DiceQuicksilverText": "Ртутное серебро, блестящее как зеркало, будто мокрое.",
    "$YA_DiceMoonstone": "Лунный камень", "$YA_DiceMoonstoneText": "Бледный эльфийский лунный камень с тонкими узорами листьев.",
    "$YA_DiceGold": "Золотые", "$YA_DiceGoldText": "Чистое золото с гранатовыми точками.",
    "$YA_DiceMalachite": "Малахитовые", "$YA_DiceMalachiteText": "Полированный стеклянно-зелёный полосатый малахит с белыми точками.",
    "$YA_DiceEbony": "Эбонитовые", "$YA_DiceEbonyText": "Чёрный эбонит с золотыми инкрустированными точками.",
    "$YA_DiceStalhrim": "Сталгримовые", "$YA_DiceStalhrimText": "Зачарованный лёд с Солстейма. Холодно-голубой, в трещинах, слабо светится.",
    "$YA_DiceDragonbone": "Из драконьей кости", "$YA_DiceDragonboneText": "Бледная драконья кость с волокнистой текстурой, точки в тёмно-красных пятнах.",
    "$YA_DiceDaedric": "Даэдрические", "$YA_DiceDaedricText": "Чёрные с красным, в рунах, точки тлеют, как угли.",
    "$YA_CatOnes": "Единицы", "$YA_CatTwos": "Двойки", "$YA_CatThrees": "Тройки", "$YA_CatFours": "Четвёрки",
    "$YA_CatFives": "Пятёрки", "$YA_CatSixes": "Шестёрки", "$YA_CatThreeKind": "Три одинаковых",
    "$YA_CatFourKind": "Четыре одинаковых", "$YA_CatFullHouse": "Фулл-хаус", "$YA_CatSmallStraight": "Малый стрит",
    "$YA_CatLargeStraight": "Большой стрит", "$YA_CatYacht": "Яхта", "$YA_CatChance": "Шанс",
}

ZH = {
    "$YA_OffTableToast": "掉出桌面！再掷一次",
    "$YA_PayoutWin": "你赢得 {0} 金币",
    "$YA_NowSelling": "旅店老板现在出售{0}骰子",
    "$YA_PayoutDraw": "你的 {0} 金币退还给你",
    "$YA_PayoutLose": "{0}拿走了你的 {1} 金币",
    "$YA_OppScores": "{0}记分 {1}：{2}",
    "$YA_Scratched": "划掉",
    "$YA_NoRollsToast": "没有掷骰次数了",
    "$YA_BoardClear": "桌面已经清空",
    "$YA_DiceFirst": "先把骰子放进骰盅或骰架上",
    "$YA_CupEmpty": "骰盅是空的",
    "$YA_NoGold": "你没有那么多金币",
    "$YA_CantAfford": "你买不起",
    "$YA_BoughtToast": "{0}骰子归你了",
    "$YA_YourOpponent": "你的对手",
    "$YA_TurnOver": "游戏结束",
    "$YA_YourTurn": "轮到你了",
    "$YA_WagerTop": "赌注 {0} 金币",
    "$YA_HintOpp": "{0}正在掷骰",
    "$YA_HintReady": "按住左键并移动来摇骰盅，松开即掷出。",
    "$YA_HintShake": "摇一摇再松开：骰盅会朝你最后移动的方向倾倒。",
    "$YA_HintRolling": "滚动中",
    "$YA_HintRedo": "掉出桌面。再掷一次。",
    "$YA_HintChoose": "点击骰子保留它。把骰子拖回骰盅重掷，或在记分卡上选一格。",
    "$YA_HintNoRolls": "没有掷骰次数了。在记分卡上选一格。",
    "$YA_CardYours": "你的",
    "$YA_Record": "战绩 {0}-{1}{2}",
    "$YA_Drawn": "，平局 {0}",
    "$YA_CardUpper": "上半区",
    "$YA_CardLower": "下半区",
    "$YA_CardBonus": "满63分奖励35",
    "$YA_CardYachtBonus": "快艇奖励",
    "$YA_KeyShout": "Fus Ro Dah",
    "$YA_KeyHelp": "玩法",
    "$YA_KeyMuted": "已静音",
    "$YA_KeySound": "声音",
    "$YA_KeyForfeit": "认输",
    "$YA_SoundTitle": "声音",
    "$YA_SoundMusic": "音乐",
    "$YA_SoundDice": "骰子与骰盅",
    "$YA_SoundEffects": "音效",
    "$YA_SoundUnmute": "取消静音",
    "$YA_SoundMuteAll": "全部静音",
    "$YA_HelpTitle": "快艇骰子",
    "$YA_Help1": "按住左键并移动，拿起骰盅摇晃。松开后骰子会朝你最后移动的方向甩出。骰子掉出桌面就要重掷。",
    "$YA_Help2": "点击骰子把它放到骰架上。把它拖回骰盅就能重掷。骰盅会等到桌面清空。",
    "$YA_Help3": "你随身携带的任何杯子都能在桌上当骰盅。每赢十局，旅店老板会卖给你一套更好的骰子。",
    "$YA_LabelCup": "骰盅",
    "$YA_LabelDice": "骰子",
    "$YA_ForfeitAsk": "认输这局？",
    "$YA_ForfeitNote": "这算作输局。{0}拿走你的 {1} 金币",
    "$YA_KeepPlaying": "继续游戏",
    "$YA_WagerWith": "与{0}玩一局快艇骰子",
    "$YA_WagerNote": "下注金币。赢了可得 {0}",
    "$YA_Purse": "你的钱包：{0} 金币",
    "$YA_PlaceBet": "下注",
    "$YA_Leave": "离开",
    "$YA_ShopStock": "{0}的货物",
    "$YA_ShopTitle": "骰子",
    "$YA_ShopPurse": "你的钱包：{0} 金币  -  胜 {1} 局",
    "$YA_ShopInUse": "使用中",
    "$YA_ShopOwned": "已拥有",
    "$YA_ShopPrice": "{0} 金币",
    "$YA_ShopWins": "胜 {0} 局",
    "$YA_ShopStarting": "初始骰子",
    "$YA_ShopStats": "价格  {0}     胜场  {1}",
    "$YA_ShopUse": "使用这套",
    "$YA_ShopBuy": "购买  {0}",
    "$YA_ShopNoGold": "金币不足",
    "$YA_ShopAfter": "胜 {0} 局后出售",
    "$YA_ShopYours": "你正在用的骰子",
    "$YA_ShopDone": "完成",
    "$YA_OverWin": "你赢了",
    "$YA_OverDraw": "平局",
    "$YA_OverForfeit": "认输",
    "$YA_OverLose": "你输了",
    "$YA_OverTitle": "游戏结束",
    "$YA_OverRecord": "你对{0}的战绩：{1}-{2}{3}",
    "$YA_OverCup": "你的骰盅：{0}",
    "$YA_Rematch": "再来一局",
    "$YA_BoughtHud": "{0}骰子归你了。下一桌就用它们。",
    "$YA_Innkeeper": "旅店老板",
    "$YA_Leaving": "正在离开牌桌",
    "$YA_SettingUp": "正在布置牌桌",
    "$YA_Cup_tankard": "大酒杯",
    "$YA_Cup_bloodtankard": "血色大酒杯",
    "$YA_Cup_glazedcup": "釉面杯",
    "$YA_Cup_goblet": "釉面高脚杯",
    "$YA_Cup_dwemer": "矮人杯",
    "$YA_Cup_dwemer2": "华丽矮人杯",
    "$YA_Cup_silver": "银质高脚杯",
    "$YA_Cup_silver2": "银圣杯",
    "$YA_DiceBone": "骨质", "$YA_DiceBoneText": "手工雕刻的骨头。泛黄、满是划痕，点孔里积着污垢。",
    "$YA_DiceIron": "铁质", "$YA_DiceIronText": "锤打的铁，坑坑洼洼带着锈斑，点是冲压出来的。",
    "$YA_DiceSteel": "钢质", "$YA_DiceSteelText": "拉丝钢，刻着清晰的点。",
    "$YA_DiceCorundum": "刚玉", "$YA_DiceCorundumText": "铜色的刚玉，边缘略微泛绿。",
    "$YA_DiceDwemer": "矮人", "$YA_DiceDwemerText": "矮人青铜，点是齿轮纹样，因年代久远而发绿。",
    "$YA_DiceOrichalcum": "山铜", "$YA_DiceOrichalcumText": "兽人锻造的山铜，深绿青铜色，布满爪痕。",
    "$YA_DiceSilver": "银质", "$YA_DiceSilverText": "抛光的银，角落发暗，点是黑色乌银。",
    "$YA_DiceQuicksilver": "水银", "$YA_DiceQuicksilverText": "镜面般明亮的水银，看起来湿漉漉的。",
    "$YA_DiceMoonstone": "月长石", "$YA_DiceMoonstoneText": "苍白的精灵月长石，带着细细的叶纹。",
    "$YA_DiceGold": "黄金", "$YA_DiceGoldText": "纯金，点是石榴石。",
    "$YA_DiceMalachite": "孔雀石", "$YA_DiceMalachiteText": "抛光的玻璃绿孔雀石，带条纹，点是白色。",
    "$YA_DiceEbony": "乌木", "$YA_DiceEbonyText": "黑色乌木，镶嵌金色的点。",
    "$YA_DiceStalhrim": "斯陶海姆", "$YA_DiceStalhrimText": "来自索瑟姆的附魔寒冰。冷蓝色，布满裂纹，微微发光。",
    "$YA_DiceDragonbone": "龙骨", "$YA_DiceDragonboneText": "苍白的龙骨，纤维纹理，点染成暗红色。",
    "$YA_DiceDaedric": "魔族", "$YA_DiceDaedricText": "黑红相间，刻满符文，点像炭火般阴燃。",
    "$YA_CatOnes": "一点", "$YA_CatTwos": "二点", "$YA_CatThrees": "三点", "$YA_CatFours": "四点", "$YA_CatFives": "五点",
    "$YA_CatSixes": "六点", "$YA_CatThreeKind": "三条", "$YA_CatFourKind": "四条", "$YA_CatFullHouse": "葫芦",
    "$YA_CatSmallStraight": "小顺", "$YA_CatLargeStraight": "大顺", "$YA_CatYacht": "快艇", "$YA_CatChance": "全选",
}


def write(name, lines):
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(b"\xff\xfe")
        f.write("\r\n".join(lines + [""]).encode("utf-16-le"))


def main():
    os.makedirs(OUT, exist_ok=True)
    en = english()
    write("SkyrimYacht_ENGLISH.txt", [f"{k}\t{v}" for k, v in en.items()])
    problems = 0
    for lang, table in (("RUSSIAN", RU), ("CHINESE", ZH)):
        for k in en:
            if k not in table:
                print(f"{lang}: no {k} (stays English)")
                problems += 1
            elif sorted(re.findall(r"\{\d\}", en[k])) != sorted(re.findall(r"\{\d\}", table[k])):
                print(f"{lang}: {k} has different placeholders")
                problems += 1
        for k in table:
            if k not in en:
                print(f"{lang}: {k} isn't in the code any more")
        write(f"SkyrimYacht_{lang}.txt", [f"{k}\t{table[k]}" for k in en if k in table])

    def where(k):
        for p, w in WHERE.items():
            if k[4:].startswith(p):
                return w
        return ""

    guide = [
        "SkyrimYacht - translating the table",
        "",
        "Everything the table shows comes from one file:",
        "    Data\\Interface\\Translations\\SkyrimYacht_<LANGUAGE>.txt",
        "where <LANGUAGE> is the game's own (sLanguage in Skyrim.ini: ENGLISH, RUSSIAN, CHINESE, POLISH, ...).",
        "To use another file, set  Language = <LANGUAGE>  under [Language] in SkyrimYacht.ini.",
        "",
        "To translate:",
        " 1. Copy SkyrimYacht_ENGLISH.txt to SkyrimYacht_<LANGUAGE>.txt and translate the text after each tab.",
        "    Leave the $YA_ key before the tab as it is. Save as UTF-16 LE (as the game's own files) or UTF-8.",
        "    xTranslator opens these files too.",
        " 2. {0}, {1}... are filled in (a name, a number): keep every one, in any order your language needs.",
        " 3. A line you leave out stays English, so a translation can be done a bit at a time.",
        " 4. Ship it as a small mod with just that file. It keeps working across SkyrimYacht updates; new lines",
        "    show in English until you add them (the log lists how many lines your file had).",
        "",
        "Letters: the table draws Latin (with accents), Greek and Cyrillic out of the box, and any other script",
        "(Chinese, Japanese, Korean) from Windows' own fonts (Microsoft YaHei, SimSun, Meiryo, Malgun Gothic).",
        "To use your own font, put a .ttf/.ttc in Data\\SKSE\\Plugins\\SkyrimYacht\\Fonts and add to your file:",
        "    $YA__FontText<tab>yourfont.ttf     (the plain text)",
        "    $YA__FontBook<tab>yourfont.ttf     (the score cards)",
        "",
        "To see which line is which in game, set  ShowKeys = 1  under [Language] in SkyrimYacht.ini:",
        "the table shows each line's key in place of its text.",
        "",
        "The dialogue (\"Care for a Yacht game?\") and the dice items' names are in SkyrimYacht.esp: translate",
        "those with xTranslator as for any plugin. The settings page in SKSE Menu Framework is English only.",
        "",
        "The lines, and where they show:",
        "",
    ]
    for k, v in en.items():
        w = where(k)
        guide.append(f"{k}\t{v}" + (f"    [{w}]" if w else ""))
    with open(os.path.join(OUT, "Translating.txt"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(guide) + "\n")
    print(f"{len(en)} lines; {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
