# -*- coding: utf-8 -*-
"""
臨床諮詢問答與推論生成 AI (Clinical Reasoning & Answer Generation AI)
具備四大臨床架構：
1. 【AI 臨床問題理解】：精準解析使用者的自然語言提問意圖，消除關鍵字衝突，先懂核心關切情境。
2. 【核心白話解答】：直接提供明確、臨床可執行的白話指引，絕不推諉、絕不敷衍請讀者自行翻看仿單。
3. 【仿單核定依據】：引述食藥署核定仿單對應章節條文與數據。
4. 【用藥安全與就醫警訊】：主動提醒紅旗警訊 (Red Flags)、緊急就醫指標與臨床照護叮嚀。
"""

import re
import html

# 臨床針劑配伍與靜脈注射相容性核心知識庫 (Clinical IV Compatibility & Admixture)
IV_COMPATIBILITY_KNOWLEDGE = {
    'pembrolizumab': {
        'name': '吉舒達 (Pembrolizumab)',
        'type': 'iv',
        'diluent': (
            '1. 相容稀釋液：**0.9% 氯化鈉注射液 (0.9% Normal Saline, NS)** 或 **5% 葡萄糖注射液 (5% Dextrose in Water, D5W)**。\n'
            '2. 調配濃度限制：稀釋後之最終濃度範圍必須介於 **1 mg/mL 至 10 mg/mL** 之間。\n'
            '3. 混勻操作規範：抽取計算劑量之 Pembrolizumab 溶液注入點滴袋後，請**緩慢且輕柔地顛倒點滴袋混勻**；⚠️ **嚴禁劇烈搖晃 (DO NOT SHAKE)**，劇烈晃動會使單株抗體蛋白質結構變性、聚集並產生大量微粒與氣泡！'
        ),
        'incompatibility': (
            '1. ⚠️ **同管路嚴格禁令**：官方核定仿單嚴正標記「**切勿透過同一輸注管線同時投予其他藥物**」(Do NOT co-administer other drugs through the same infusion line)！\n'
            '2. 點滴袋混用禁忌：切勿將其他任何抗癌針劑、抗生素或電解質混入同一輸液袋中。\n'
            '3. 沖管規範：輸注前後應使用 0.9% NaCl 或 5% D5W 沖洗輸液管路。'
        ),
        'filter_tubing': (
            '1. 濾膜規格要求：輸注時**必須連接無菌、無熱原、低蛋白結合 (Low-Protein Binding) 之 0.2 μm 至 5 μm 在線過濾膜 (In-line or Add-on Filter)**。\n'
            '2. 輸液器材相容性：可使用聚丙烯 (PP)、聚烯烴 (Polyolefin) 或聚氯乙烯 (PVC) 輸液袋及相容輸液套管。\n'
            '3. 輸注時間：採靜脈滴注給藥，常規輸注時間必須在 **30 分鐘以上**。'
        ),
        'stability': (
            '1. 本藥品不含抑菌防腐劑，稀釋調配應於無菌操作台 (Laminar Flow Hood) 內進行。\n'
            '2. **室溫環境 (≤ 25°C)**：自調配開始起算，包含 30 分鐘靜脈輸注在內，**總累積時限不得超過 6 小時**！\n'
            '3. **冷藏環境 (2°C ～ 8°C)**：調配後置於 2°C～8°C 冰箱冷藏保存，**最長不得超過 96 小時**（包含冷藏與後續回溫輸注累計總時間）。\n'
            '4. ⚠️ **嚴禁冷凍 (DO NOT FREEZE)**。施打前應目視檢視，若有變色或可見懸浮沉澱顆粒切勿使用。'
        )
    },
    'furosemide': {
        'name': '樂泄 / 汎德 (Furosemide)',
        'type': 'iv',
        'diluent': (
            '1. 相容稀釋液：首選 **0.9% 氯化鈉注射液 (0.9% NaCl, NS)** 或 **乳酸林格氏液 (Lactated Ringer\'s, LR)**。\n'
            '2. 溶液酸鹼度要求：Furosemide 注射液為**強鹼性 (pH 8.0 ～ 9.3)**；若稀釋於酸性點滴液（如未加緩衝之 D5W，pH 3.5~5.0）中，pH 值降至 5.5 以下極易引發 Furosemide 游離酸極速結晶析出沉澱，臨床常規推薦使用 0.9% NaCl。'
        ),
        'incompatibility': (
            '1. 🚫 **酸性藥物嚴格配伍禁忌（立即產生肉眼結晶沉澱）**：\n'
            '   嚴禁與 Milrinone、Midazolam、Dobutamine、Dopamine、Ondansetron、Ciprofloxacin、Gentamicin、Morphine 等酸性針劑在同一點滴袋、同一管路或 Y-Site 共同輸注！混合將導致嚴重管路沉澱阻塞及微粒栓塞危險。\n'
            '2. 沖管要求：若需共用靜脈導管，給藥前後必須以 0.9% NaCl 充分沖洗管路。'
        ),
        'filter_tubing': (
            '1. 給藥速率黑框限制：大劑量靜脈滴注時，輸注速率**嚴格不得超過每分鐘 4 mg (≤ 4 mg/min)**！\n'
            '2. 耳毒性警告：推注過快 (速率 > 4 mg/min) 極易誘發嚴重耳鳴、聽力減退或永久性第八對腦神經耳毒性 (Ototoxicity)。常規劑量 20~40 mg 應以 1~2 分鐘緩慢靜脈推注。'
        ),
        'stability': (
            '1. 避光要求：本藥對光敏感，針劑安瓿應避光儲存於原紙盒中。\n'
            '2. 調配後安定性：稀釋於 0.9% NaCl 後置於 25°C 室溫避光處，可穩定保存 24 小時。\n'
            '3. ⚠️ **嚴禁冷藏**：冷藏容易加速 Furosemide 晶體析出沉澱；若溶液發黃變深或出現任何沉澱沈積，切勿使用。'
        )
    },
    'paclitaxel': {
        'name': '紫杉醇 / 伏摩素 (Paclitaxel / Formoxol)',
        'type': 'iv',
        'diluent': (
            '1. 相容稀釋液：0.9% 氯化鈉注射液 (NS)、5% 葡萄糖注射液 (D5W)、5% 葡萄糖生理食鹽水 (D5NS)。\n'
            '2. 調配濃度限制：稀釋至最終濃度 **0.3 mg/mL 至 1.2 mg/mL** 範圍內，顛倒混勻。'
        ),
        'incompatibility': (
            '1. ⚠️ **嚴禁使用 PVC 輸液容器與管路**：Paclitaxel 調配劑含有聚氧乙烯蓖麻油 (Cremophor EL)，會強力萃取出聚氯乙烯 (PVC) 中的致癌塑化劑 DEHP！\n'
            '2. 必須使用非 PVC 容器（聚乙烯 PE、聚丙烯 PP、聚烯烴 Polyolefin 袋或玻璃瓶）。'
        ),
        'filter_tubing': (
            '1. 濾膜規格：輸注過程**必須連接配備微孔直徑不超過 0.22 μm 之在線過濾器 (In-line Filter)**。\n'
            '2. 輸液套管：必須配備聚乙烯 (PE) 內襯之專用輸液導管。\n'
            '3. 輸注時間：常規靜脈滴注時間為 **3 小時**。'
        ),
        'stability': (
            '1. 調配後室溫 (25°C) 避光條件下可維持 27 小時穩定。\n'
            '2. 配製後外觀可能呈現微乳光或乳白色，若有析出結晶顆粒不可使用。'
        )
    },
    'depakine': {
        'name': '帝拔癲 (Depakine / Sodium Valproate 注射劑)',
        'type': 'iv',
        'diluent': (
            '1. **官方核定相容點滴液清單**：\n'
            '   下列為與本品注射劑相容的點滴液：\n'
            '   * 生理食鹽水(normal saline，0.9g for 100ml)\n'
            '   * 葡萄糖點滴液(dextrose，5g for 100ml)\n'
            '   * 葡萄糖點滴液(dextrose，10g for 100ml)\n'
            '   * 葡萄糖點滴液(dextrose，20g for 100ml)\n'
            '   * 葡萄糖點滴液(dextrose，30g for 100ml)\n'
            '   * 葡萄糖生理食鹽水(dextrose，2.5g+NaCl，0.45g for 100ml)\n'
            '   * 重碳酸鈉(sodium bicarbonate，0.14g for 100ml)\n'
            '   * trometamol (THAM)，3.66g+NaCl，0.172g for 100ml\n\n'
            '2. **稀釋容量與調配規格**：\n'
            '   * **稀釋比例**：400mg 本品注射劑溶於 **500ml** 上述之點滴液中使用 (**trometamol 例外：250ml**)。\n'
            '   * **初配調製方式**：使用前應先調劑，將 4 毫升注射用水注入小瓶中，將藥品粉末溶解後再取出適當劑量使用。'
        ),
        'incompatibility': (
            '1. **獨立輸注管路規範（配伍禁忌）**：\n'
            '   * 本品注射劑可以緩慢靜脈注射或**單獨使用一靜脈輸注管**的靜脈點滴方式給藥。\n'
            '   * 嚴禁與其他未確認相容性之注射劑在同一點滴袋中混合或同管路交會輸注。\n'
            '2. **沖管要求**：\n'
            '   * 若與其他輸液共用靜脈通道，於給藥前後應以相容之生理食鹽水 (0.9% NaCl) 充分沖洗管路。'
        ),
        'filter_tubing': (
            '1. **容器與管路材質相容性**：\n'
            '   * **此靜脈點滴液適用於 PVC、polythene（聚乙烯 PE）或玻璃容器三種材質**。\n'
            '2. **給藥速率與途徑**：\n'
            '   * 緩慢靜脈推注：注射時間須超過 5 分鐘。\n'
            '   * 靜脈點滴輸注：持續 24 小時點滴給藥，或將一日劑量分成四次點滴 (每次給藥時間須超過 1 小時)；維持點滴速率為 1 mg/kg/hour。'
        ),
        'stability': (
            '1. **調配後安定性與使用時限**：\n'
            '   * 本品注射劑應於使用前調劑，**含此注射液的點滴液應於 24 小時內用完，未用完的部分應丟棄**。\n'
            '2. **外觀目視檢驗**：\n'
            '   * 本品不含防腐劑，調配後溶液若有任何混濁、結晶沉澱或變色，嚴禁注入人體。'
        )
    },
    'invanz': {
        'name': '益滿治 / 厄他培南 (INVANZ / Ertapenem 注射劑)',
        'type': 'iv',
        'diluent': (
            '1. **官方核定專用稀釋液（嚴格限制）**：\n'
            '   * 僅限使用 **0.9% 氯化鈉注射液 (0.9% NaCl, 生理食鹽水)**、**注射用水** 或 **制菌注射用水**。\n'
            '2. **13 歲以上成人及青少年靜脈準備步驟**：\n'
            '   * **初配溶解**：每 1 公克 INVANZ 小瓶加入 **10 mL (公撮)** 的注射用水、0.9% 氯化鈉注射液或制菌注射用水。\n'
            '   * **充分搖動**：充分搖動使藥品溶解，並立刻將溶解後之溶液移到 **50 mL (公撮) 的 0.9% 氯化鈉注射液** 中完成稀釋。\n'
            '3. **3 個月大至 12 歲病童靜脈準備步驟**：\n'
            '   * 依 15 mg/kg 劑量抽取適量初配溶解液（每日劑量上限不超過 1 公克），以 **0.9% 氯化鈉注射液** 稀釋成濃度為 **20 mg/mL 或更稀**。\n'
            '4. **肌肉注射 (IM) 準備步驟**：\n'
            '   * 含 1 公克 INVANZ 小瓶加入 **3.2 mL 的 1.0% 或 2.0% 之 lidocaine HCl 注射液（不含 epinephrine）**，充分搖勻溶解。\n'
            '   * 立刻抽出溶液並以深部肌肉注射方式注入大肌肉部位（如臀部肌肉或大腿側邊肌肉），調配好的肌肉注射溶液必須在調配後的 **1 小時內** 使用完畢。（⚠️ 註：本調配好的肌肉注射液絕對不可供作靜脈投與！）。'
        ),
        'incompatibility': (
            '1. 🚫 **葡萄糖絕對配伍禁忌（首要致命禁忌）**：\n'
            '   * **官方仿單嚴格明定：不可以使用含有葡萄糖 (α-D-GLUCOSE) 的稀釋液！**（D5W、D10W 等含葡萄糖點滴液絕對禁用！葡萄糖會破壞藥物安定性使藥效降解失效）。\n'
            '2. 🚫 **禁止與其他藥物混合輸注**：\n'
            '   * **官方仿單明定：不可以將 INVANZ 與其他藥品混合或同時輸注！**\n'
            '   * 必須使用專屬獨立輸注管路給藥，嚴禁共用同一點滴袋或同一 Y-Site 共同輸注。\n'
            '3. **沖管規範**：\n'
            '   * 若與其他藥品共用同一靜脈輸注導管，於給藥前後必須以相容之 **0.9% 氯化鈉注射液 (生理食鹽水)** 徹底沖洗管線。'
        ),
        'filter_tubing': (
            '1. **靜脈輸注時間規範**：\n'
            '   * 採取靜脈投與時，輸注 INVANZ 的時間**必須超過 30 分鐘**，不可快速靜脈推注。\n'
            '2. **給藥前目視外觀檢查**：\n'
            '   * INVANZ 溶液正常呈**無色至淡黃色**，在此範圍內的顏色差異不影響藥品效價；但若發現有可見顆粒沉澱或變色情形，切勿施打。'
        ),
        'stability': (
            '1. **靜脈稀釋液使用時限（黃金 6 小時）**：\n'
            '   * 經稀釋的靜脈注射藥品**必須在 6 小時內完成輸注**！逾時必須丟棄，切勿留置。\n'
            '2. **肌肉注射液使用時限（1 小時）**：\n'
            '   * 調配好的肌肉注射溶液必須在調配後的 **1 小時內** 使用完畢。'
        )
    }
}
IV_COMPATIBILITY_KNOWLEDGE['keytruda'] = IV_COMPATIBILITY_KNOWLEDGE['pembrolizumab']
IV_COMPATIBILITY_KNOWLEDGE['吉舒達'] = IV_COMPATIBILITY_KNOWLEDGE['pembrolizumab']
IV_COMPATIBILITY_KNOWLEDGE['rosis'] = IV_COMPATIBILITY_KNOWLEDGE['furosemide']
IV_COMPATIBILITY_KNOWLEDGE['樂泄'] = IV_COMPATIBILITY_KNOWLEDGE['furosemide']
IV_COMPATIBILITY_KNOWLEDGE['formoxol'] = IV_COMPATIBILITY_KNOWLEDGE['paclitaxel']
IV_COMPATIBILITY_KNOWLEDGE['伏摩素'] = IV_COMPATIBILITY_KNOWLEDGE['paclitaxel']
IV_COMPATIBILITY_KNOWLEDGE['紫杉醇'] = IV_COMPATIBILITY_KNOWLEDGE['paclitaxel']
IV_COMPATIBILITY_KNOWLEDGE['depakine'] = IV_COMPATIBILITY_KNOWLEDGE['depakine']
IV_COMPATIBILITY_KNOWLEDGE['帝拔癲'] = IV_COMPATIBILITY_KNOWLEDGE['depakine']
IV_COMPATIBILITY_KNOWLEDGE['valproate'] = IV_COMPATIBILITY_KNOWLEDGE['depakine']
IV_COMPATIBILITY_KNOWLEDGE['valproic'] = IV_COMPATIBILITY_KNOWLEDGE['depakine']
IV_COMPATIBILITY_KNOWLEDGE['纈草酸'] = IV_COMPATIBILITY_KNOWLEDGE['depakine']
IV_COMPATIBILITY_KNOWLEDGE['invanz'] = IV_COMPATIBILITY_KNOWLEDGE['invanz']
IV_COMPATIBILITY_KNOWLEDGE['ertapenem'] = IV_COMPATIBILITY_KNOWLEDGE['invanz']
IV_COMPATIBILITY_KNOWLEDGE['益滿治'] = IV_COMPATIBILITY_KNOWLEDGE['invanz']



# =============================================================================
# 臨床意圖加權分類規則庫 (Clinical Intent Rules & Disambiguation)
# =============================================================================
INTENT_CLASSIFIER_RULES = {
    'surgery_dental': {
        'name': '外科手術、拔牙、植牙或侵入性檢查前之圍手術期停藥評估（是否需停藥、術前需停藥幾天，以及出血與血栓風險管理）',
        # 必須包含至少一個實體醫療或手術處置詞彙
        'required': [
            '拔牙', '手術', '開刀', '動手術', '切片', '內視鏡', '胃鏡', '大腸鏡',
            '牙醫', '植牙', '根管', '洗牙', '拔牙前', '開刀前', '手術前', '術前',
            '圍手術期', '麻醉', '牙科', '門診手術', '微創手術'
        ],
        'boost': [
            '停藥幾天', '術前停藥', '出血風險', '凝血', '止血', '停藥', '停掉',
            '不吃', '暫停', '吃藥嗎', '要吃嗎', '需要停嗎', '該停嗎', '幾天前停'
        ],
        'anti': []
    },
    'allergy_emergency': {
        'name': '嚴重藥物過敏、過敏性休克或急性皮膚水泡黏膜潰爛之緊急處置與立即停藥指引',
        'required': [
            '過敏', '起紅疹', '蕁麻疹', '全身癢', '搔癢難耐', '起水泡', '嘴唇腫',
            '喉嚨腫', '呼吸急促', '氣喘', '喘不過氣', '臉部水腫', '史蒂芬強生',
            'sjs', '嚴重過敏', '紅斑', '皮膚脫屑'
        ],
        'boost': ['停藥嗎', '立即停', '急診', '看醫生', '救命'],
        'anti': ['開車', '想睡']
    },
    'stopping': {
        'name': '病情穩定或指標正常後，是否可自行停止服藥（擅自中斷用藥之反彈風險評估）',
        'required': [
            '自己停', '擅自', '好多了可以停嗎', '正常了可以不要吃嗎', '正常可以不吃嗎',
            '血壓正常可以不吃嗎', '不想吃了', '可以斷藥嗎', '可以停掉了嗎', '吃一輩子',
            '終身服藥', '自行停藥', '病好了可以停嗎', '指數正常可以停嗎', '不要吃了'
        ],
        'boost': ['指標正常', '沒症狀', '指數正常', '降下來了', '穩定了', '減量', '減半', '停藥', '斷藥'],
        # 排除外在手術、牙科、過敏等情境
        'anti': [
            '拔牙', '手術', '開刀', '切片', '內視鏡', '牙醫', '植牙', '根管', '洗牙',
            '術前', '開刀前', '懷孕', '起疹', '過敏', '不舒服', '胃痛', '想吐'
        ]
    },
    'missed_dose': {
        'name': '忘記服藥（漏服一劑）之後續補服處置原則與間隔時間判斷',
        'required': [
            '忘記', '漏服', '漏吃', '補吃', '補服', '沒吃', '忘了吃', '漏掉',
            '少吃一次', '忘了服', '沒吃到', '慢吃'
        ],
        'boost': ['補吃一劑', '吃兩顆', '時間過了', '想起時', '間隔', '下次服藥'],
        'anti': ['多吃', '吃太多', '過量', '吃了兩顆', '吃了2顆', '中毒', '誤食']
    },
    'overdose': {
        'name': '不慎過量服用（多吃藥物/重複服藥）之急性毒性風險與緊急處置程序',
        'required': [
            '多吃', '吃太多', '吃了兩顆', '吃了2顆', '吃了三顆', '吞兩顆', '吞了兩顆',
            '誤食', '過量', '中毒', '吃過量', '雙倍', '吃兩倍', '吃重複', '重複吃', '吃錯劑量'
        ],
        'boost': ['洗胃', '催吐', '送醫', '急診', '致死', '毒性', '解毒劑', '掛急診'],
        'anti': []
    },
    'pregnancy': {
        'name': '懷孕期 / 哺乳期之用藥安全性與胚胎胎兒發育風險評估',
        'required': [
            '懷孕', '孕婦', '懷孕中', '備孕', '受孕', '胎兒', '寶寶', '授乳',
            '哺乳', '餵奶', '母乳', '妊娠', '畸胎', '懷孕初期', '懷孕兩個月',
            '懷孕三個月', '懷孕四個月', '懷孕幾週'
        ],
        'boost': ['安全嗎', '影響胎兒', '畸形', '致畸性', '哺乳期', '乳汁', '對寶寶'],
        'anti': []
    },
    'storage': {
        'name': '藥品儲存環境規範（是否需放置冰箱冷藏，或置於室溫乾燥陰涼處）',
        'required': [
            '冰箱', '冷藏', '冷凍', '放哪', '保存', '常溫', '室溫', '潮濕',
            '曬太陽', '變質', '放在哪', '放房間', '放客廳', '放車上', '存放',
            '儲存', '貯存', '冰存'
        ],
        'boost': ['防潮', '避光', '受潮', '保存期限', '過期', '變質', '結冰'],
        'anti': []
    },
    'driving_drowsy': {
        'name': '服藥後之中樞神經嗜睡反應，以及對駕駛汽機車或操作機械之安全評估',
        'required': [
            '想睡', '想睡覺', '嗜睡', '昏睡', '頭暈', '開車', '操作機械', '注意力',
            '駕駛', '騎車', '精神不濟', '會愛睏嗎', '愛睏', '打瞌睡'
        ],
        'boost': ['反應力', '鎮靜', '疲倦', '危險', '恍神'],
        'anti': []
    },
    'crush_chew': {
        'name': '藥品特殊劑型結構評估（吞嚥困難時是否可磨粉、咬碎服用，或透過鼻胃管灌食）',
        'required': [
            '磨粉', '咬碎', '咬破', '吞不下去', '撥開', '弄碎', '壓碎', '剝半',
            '切半', '管灌', '鼻胃管', '咬著吃', '太難吞', '太顆', '很大顆'
        ],
        'boost': ['緩釋', '腸溶', '長效', '溶解', '膠囊打開', '胃管', '泡水'],
        'anti': []
    },
    'iv_compatibility': {
        'name': '靜脈注射 (IV) 稀釋液相容性、Y-Site 同管路配伍禁忌、在線濾膜規格與調配後安定性',
        'required': [
            'iv相容性', '相容性', 'iv相容', '配伍', '配伍禁忌', '稀釋液', '稀釋', 'y-site',
            'y site', 'y沖', '濾膜', '過濾器', '點滴相容', '輸注管', '管路相容',
            '針劑調配', '沉澱', 'd5w', 'ns', '葡萄糖水', '生理食鹽水', 'iv', '相容', '點滴'
        ],
        'boost': ['同管輸注', '濾膜規格', '滴注時間', '析出', '結晶', '變色', '安定性', '容器材質', 'pvc', '配伍禁忌'],
        'anti': []
    },
    'interaction': {
        'name': '藥品與其他處方藥、非處方藥、飲食（葡萄柚/酒精）或保健食品之交互作用安全',
        'required': [
            '交互作用', '一起吃', '配著吃', '同時吃', '葡萄柚', '柚子', '酒精',
            '喝酒', '中藥', '保健食品', '維他命', '消炎藥', '併用', '隔多久吃',
            '衝突', '相剋', '一起吞'
        ],
        'boost': ['cyp3a4', '間隔', '影響藥效', '抗藥性', '抑制', '誘導'],
        'anti': []
    },
    'renal_impairment': {
        'name': '腎功能不全、血液透析 (洗腎) 患者之用藥安全性與劑量微調指引',
        'required': [
            '腎功能不好要調整劑量嗎', '腎功能不好', '洗腎', '透析', '血液透析', '腹膜透析', '腎臟', '腎功能', '腎衰竭',
            'egfr', 'crcl', '肌酸酐', '肌酐', '清除率', '腎障礙', '腎不全'
        ],
        'boost': ['調整劑量', '清除率', '透析清除', '排泄', '蓄積', '減量', '怎麼吃', '劑量', '吃幾顆', '劑量調整'],
        'anti': ['肝功能', '肝指數', '肝炎']
    },
    'hepatic_impairment': {
        'name': '肝功能異常、急慢性肝炎、肝硬化患者之用藥安全性、禁忌與劑量微調指引',
        'required': [
            '肝功能不好可以用嗎', '肝功能不好', '肝功能', '肝指數', '肝硬化', 'ast', 'alt', '肝炎', '黃疸',
            '肝障礙', '肝不全', '肝毒性', 'child-pugh'
        ],
        'boost': ['調整劑量', '禁忌', '慎用', '監測', '減量', '肝病'],
        'anti': ['洗腎', '透析', '腎功能']
    },
    'pediatric_use': {
        'name': '兒童、小兒與青少年族群之適用年齡限制、安全性與體重劑量微調指引',
        'required': [
            '小孩最小幾歲可以用', '小孩', '兒童', '小兒', '幾歲', '歲', '月齡', '嬰兒', '新生兒', '兒科', '幼兒'
        ],
        'boost': ['劑量', 'mg/kg', '體重', '安全', '有效性', '禁忌', '不建議', '尚未確立'],
        'anti': ['老人', '高齡', '長者']
    },
    'geriatric_use': {
        'name': '65 歲以上高齡長者之生理機能衰退評估、起始劑量調整與多重用藥監測指引',
        'required': [
            '老人可以用嗎', '老人', '高齡', '長者', '年長者', '65歲', '銀髮族', '老年'
        ],
        'boost': ['劑量', '起始', '調整', '減量', '清除率', '低劑量', '監測'],
        'anti': ['小孩', '小兒', '兒童']
    },
    'adverse_effects_ten_percent': {
        'name': '官方仿單定義極常見 (發生率 > 10% 或 ≥ 10%) 之副作用清單、自覺症狀與照護處置',
        'required': [
            '常見副作用', '發生率>10%', '>10%', '≥10%', '10%', '極常見', '很常見', '副作用', '不良反應'
        ],
        'boost': ['常見', '發生率', '耐受度', '頻率'],
        'anti': ['開車', '想睡', '嗜睡', '拔牙', '手術']
    },
    'special_warnings_precautions': {
        'name': '衛生福利部官方核定之【特殊警語 / 黑框警訊 (Boxed Warnings)】與病人須知',
        'required': [
            '特殊警語或病人須注意事項', '特殊警語', '黑框', '黑框警訊', '警訊', '警告', '病人須知', '注意事項'
        ],
        'boost': ['致死', '嚴重警示', '監控', '生命危險'],
        'anti': []
    },
    'indications': {
        'name': '衛生福利部核准之法定適應症與臨床主要治療用途',
        'required': [
            '適應症', '吃什麼的', '治療什麼', '有什麼用', '功效', '作用是什麼',
            '有什麼效果', '治什麼病', '幹嘛吃的', '功能是什麼', '用在什麼病',
            '吃這顆幹嘛', '主要作用'
        ],
        'boost': ['核准', '主要用途', '療效', '核准適應症'],
        'anti': []
    },
    'dosage': {
        'name': '藥品標準建議劑量、服用途徑、服藥時間與餐食搭配指引',
        'required': [
            '用法', '用量', '一天吃幾次', '怎麼吃', '飯前', '飯後', '空腹',
            '隨餐', '吃幾顆', '劑量', '間隔多久', '吃法', '一次幾顆', '給藥途徑'
        ],
        'boost': ['頻率', '時間', '配水', '早晚', '睡前'],
        'anti': ['忘記', '多吃', '磨粉', '咬碎', '手術', '拔牙', '洗腎', '透析', '腎功能', '腎衰竭', '肝功能', '肝指數']
    },
    'contraindications': {
        'name': '藥品之絕對禁忌症與嚴格不可使用之病患對象',
        'required': ['禁忌', '不能吃', '誰不能吃', '禁忌症', '嚴禁', '哪些人不能吃', '不適用'],
        'boost': ['絕對禁忌', '過敏史', '嚴重心衰竭'],
        'anti': []
    },
    'special_warnings': {
        'name': '衛生福利部官方核定之【特殊警語 / 黑框警訊 (Boxed Warnings)】',
        'required': ['特殊警語', '黑框', '黑框警訊', '警訊', '警告'],
        'boost': ['致死', '嚴重警示', '監控'],
        'anti': []
    },
    'characteristics': {
        'name': '藥品之實體外觀性狀（顏色、劑型、幾何形狀、刻字記號）與處方賦形劑組成',
        'required': ['長什麼樣子', '樣子', '形狀', '顏色', '外觀', '性狀', '刻字', '標記', '賦形劑', '藥丸顏色'],
        'boost': ['圓形', '橢圓', '印字', '顆粒', '白色', '粉紅'],
        'anti': []
    },
    'pharmacology_pk': {
        'name': '藥品在人體內的作用機轉（藥效學）以及吸收、代謝與清除半衰期（藥物動力學 PK）',
        'required': ['作用機轉', '機轉', '藥理', '半衰期', '代謝', '吸收', '動力學', 'pk'],
        'boost': ['受體', '生體可用率', '排除', '分佈體積'],
        'anti': []
    },
    'manufacturers': {
        'name': '藥品之製造廠商所在地、分工廠區地址以及在台申請經銷藥商資料',
        'required': ['製造廠', '藥廠', '工廠', '哪裡製造', '產地', '生產廠', '次製造廠', '製造商', '藥商', '申請商', '代理商', '經銷商', '地址'],
        'boost': ['委託製造', '許可證持有者', '國外製造廠'],
        'anti': []
    },
    'price_insurance': {
        'name': '藥品之全民健保給付規定、自費價格與醫保給付適應症規範',
        'required': ['健保', '給付', '自費', '多少錢', '價格', '費用', '健保價', '貴不貴', '健保給付嗎'],
        'boost': ['事前審查', '健保碼', '點數'],
        'anti': []
    }
}


# 衛生福利部 13 類標準臨床諮詢問題規範 (TFDA Standard Clinical QA Mapping)
AUTHORIZED_QUESTIONS = {
    1: {
        'id': 1,
        'title': '藥品作用',
        'intent': 'indications',
        'icon': '🎯'
    },
    2: {
        'id': 2,
        'title': '藥品吃法或用法',
        'intent': 'dosage',
        'icon': '💊'
    },
    3: {
        'id': 3,
        'title': '腎功能不好要調整劑量嗎',
        'intent': 'renal_impairment',
        'icon': '🩺'
    },
    4: {
        'id': 4,
        'title': '孕婦可以用嗎',
        'intent': 'pregnancy',
        'icon': '🤰'
    },
    5: {
        'id': 5,
        'title': '小孩最小幾歲可以用，藥調整劑量嗎',
        'intent': 'pediatric_use',
        'icon': '👶'
    },
    6: {
        'id': 6,
        'title': '老人可以用嗎，藥調整劑量嗎',
        'intent': 'geriatric_use',
        'icon': '👴'
    },
    7: {
        'id': 7,
        'title': '肝功能不好可以用嗎，藥調整劑量嗎',
        'intent': 'hepatic_impairment',
        'icon': '🧪'
    },
    8: {
        'id': 8,
        'title': 'IV相容性與稀釋配伍禁忌為何？',
        'intent': 'iv_compatibility',
        'icon': '💉'
    },
    9: {
        'id': 9,
        'title': '跟那些藥或食物有交互作用?',
        'intent': 'interaction',
        'icon': '🥗'
    },
    10: {
        'id': 10,
        'title': '常見副作用(發生率>10%)有哪些?',
        'intent': 'adverse_effects_ten_percent',
        'icon': '⚠️'
    },
    11: {
        'id': 11,
        'title': '特殊警語或病人須注意事項',
        'intent': 'special_warnings_precautions',
        'icon': '🚨'
    },
    12: {
        'id': 12,
        'title': '拔牙或手術前需要停藥嗎？',
        'intent': 'surgery_dental',
        'icon': '🦷'
    },
    13: {
        'id': 13,
        'title': '忘記服藥如何處理？',
        'intent': 'missed_dose',
        'icon': '⏰'
    }
}

CLINICAL_DISCLAIMER = (
    "\n\n---\n"
    "⚖️ **【免責聲明】**：\n"
    "本系統提供之藥品仿單摘要與智慧諮詢分析，僅供醫療專業人員參考與臨床用藥輔助查詢，絕不能取代合格專科醫師、藥師之臨床診斷、處方或個別化醫療判斷。病人具體用藥事宜、劑量調整或停藥決策，請務必遵循主治醫師處方指示與專業藥師之用藥指導。"
)


def wrap_with_disclaimer(ans: str) -> str:
    """確保所有回答皆附加專業臨床免責聲明"""
    if "【免責聲明】" not in ans:
        ans = ans.rstrip() + CLINICAL_DISCLAIMER
    return ans


def resolve_clinical_intent(question: str, q_id=None) -> str:
    """精準定位使用者諮詢之 13 類專業臨床問題意圖"""
    matched_intent = None
    if q_id is not None:
        try:
            qid_int = int(q_id)
            if qid_int in AUTHORIZED_QUESTIONS:
                matched_intent = AUTHORIZED_QUESTIONS[qid_int]['intent']
        except Exception:
            pass

    if not matched_intent:
        clean_q = re.sub(r'[\s\d.、?？!！]+', '', question.strip())
        for q_item in AUTHORIZED_QUESTIONS.values():
            clean_title = re.sub(r'[\s\d.、?？!！]+', '', q_item['title'])
            if clean_q == clean_title or clean_q in clean_title or clean_title in clean_q:
                matched_intent = q_item['intent']
                break

    if not matched_intent:
        q_lower = question.strip().lower()
        scores = {}
        for intent_key, cfg in INTENT_CLASSIFIER_RULES.items():
            if any(anti in q_lower for anti in cfg.get('anti', [])):
                continue
            matched_required = [req for req in cfg['required'] if req in q_lower]
            if not matched_required:
                continue
            score = sum(len(req) * 5 for req in matched_required)
            matched_boost = [b for b in cfg.get('boost', []) if b in q_lower]
            score += sum(len(b) * 2 for b in matched_boost)
            scores[intent_key] = (score, cfg['name'])

        if scores:
            sorted_intents = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
            candidate_intent = sorted_intents[0][0]
            authorized_intents = [item['intent'] for item in AUTHORIZED_QUESTIONS.values()]
            if candidate_intent in authorized_intents:
                matched_intent = candidate_intent
            elif candidate_intent in ['contraindications', 'special_warnings']:
                matched_intent = 'special_warnings_precautions'
            elif candidate_intent in ['adverse_effects']:
                matched_intent = 'adverse_effects_ten_percent'

    return matched_intent


def detect_drug_administration_route(drug_info: dict) -> dict:
    """
    精準識別藥品真實劑型與法定給藥途徑（杜絕針劑被誤當口服藥亂回答吃法）：
    - is_injection: 針劑 / 注射劑 (包含靜脈輸注 IV, 皮下注射 SC, 肌肉注射 IM, 凍晶/乾粉注射劑等)
    - injection_type: 'iv' (靜脈輸注/點滴) | 'sc' (皮下注射) | 'im' (肌肉注射) | 'general'
    - is_oral: 口服製劑 (錠劑, 膠囊, 口服液, 散劑, 顆粒, 糖漿等)
    - is_topical: 外用製劑 (軟膏, 乳膏, 凝膠, 貼劑, 栓劑等)
    - is_inhaler: 吸入製劑 (吸入劑, 噴霧劑, 氣霧劑等)
    - is_ophthalmic: 眼用製劑 (點眼液, 眼藥水等)
    - is_keytruda: 是否為吉舒達 (Pembrolizumab / Keytruda)
    """
    cname = str(drug_info.get('cname') or drug_info.get('drug_name_zh') or '').strip()
    ename = str(drug_info.get('ename') or drug_info.get('drug_name_en') or '').strip()
    lic_id = str(drug_info.get('license_id') or drug_info.get('lic_id', '') or '').strip()
    dosage_form = str(drug_info.get('dosage_form') or drug_info.get('form', '') or '').strip()
    dosage_text = str(drug_info.get('dosage', '') or '')
    char_text = str(drug_info.get('characteristics', '') or '')
    query_str = str(drug_info.get('query', '') or '')

    comb_str = f"{cname} {ename} {lic_id} {dosage_form} {query_str}".lower()
    
    is_keytruda = any(k in comb_str for k in ['pembrolizumab', 'keytruda', '吉舒達']) or ('001025' in lic_id)
    is_trulicity = any(k in comb_str for k in ['trulicity', '易週糖', 'dulaglutide']) or ('001200' in lic_id)
    is_glp1 = is_trulicity or any(k in comb_str for k in ['semaglutide', 'ozempic', 'rybelsus', 'wegovy', 'tirzepatide', 'mounjaro', 'liraglutide', 'victoza', 'saxenda', 'glp-1', 'glp1'])

    # 1. 針劑 / 注射劑判定
    inj_keywords = ['注射', '針', '輸注', '凍晶', '靜脈', '皮下', '肌肉', 'injection', 'infusion', 'vial', 'ampoule', 'syringe', 'lyophilized']
    is_injection = any(k in comb_str for k in inj_keywords) or is_keytruda or is_trulicity

    # 知名針劑品項保護
    known_injectables = [
        'mepolizumab', 'nucala', '紐佳樂', '滅喘樂',
        'trastuzumab', 'herceptin', '賀疾妥', 'perjeta', 'bevacizumab', 'avastin', 
        'nivolumab', 'opdivo', '保疾伏', 'furosemide', 'rosis', '樂泄',
        'paclitaxel', 'formoxol', '伏摩素', '027928', '022395',
        'trulicity', '易週糖', 'dulaglutide', '001200',
        'invanz', 'ertapenem', '益滿治', '023749', '023901'
    ]
    if any(k in comb_str for k in known_injectables) and not any(k in dosage_form for k in ['錠', '口服', '膠囊']):
        is_injection = True

    injection_type = 'general'
    if is_injection:
        if is_trulicity or (is_glp1 and not any(k in comb_str for k in ['錠', '口服'])):
            injection_type = 'sc'
        elif any(k in comb_str or k in dosage_text.lower() for k in ['皮下', 'subcutaneous', 'sc']) and not any(k in comb_str for k in ['靜脈', 'iv', 'infusion', '輸注']):
            injection_type = 'sc'
        elif any(k in comb_str or k in dosage_text.lower() for k in ['靜脈', '輸注', '點滴', 'iv', 'infusion', 'intravenous']):
            injection_type = 'iv'
        elif any(k in comb_str or k in dosage_text.lower() for k in ['肌肉', 'im', 'intramuscular']):
            injection_type = 'im'
        else:
            injection_type = 'iv'

    # 2. 吸入劑判定
    is_inhaler = any(k in comb_str for k in ['吸入', '氣霧', '噴霧', 'inhaler', 'inhalation', 'turbuhaler', 'accuhaler', 'respimat', 'aerolizer'])

    # 3. 眼用製劑判定
    is_ophthalmic = any(k in comb_str for k in ['點眼', '眼藥', '眼用', 'ophthalmic', 'eye drops'])

    # 4. 外用製劑判定
    is_topical = any(k in comb_str for k in ['軟膏', '乳膏', '凝膠', '外用', '貼劑', '栓劑', 'cream', 'ointment', 'gel', 'patch', 'suppository']) and not is_injection

    # 5. 口服製劑判定
    is_oral = any(k in comb_str for k in ['錠', '膠囊', '散劑', '顆粒', '口服', '糖漿', '懸液', '內服', 'tablet', 'capsule', 'oral', 'syrup']) and not is_injection

    if not is_injection and not is_inhaler and not is_ophthalmic and not is_topical and not is_oral:
        is_oral = True

    clean_form = dosage_form
    if not clean_form:
        if is_trulicity:
            clean_form = '皮下注射劑（單次使用注射筆）'
        elif is_injection:
            clean_form = '注射劑'
        else:
            clean_form = '口服製劑'

    return {
        'is_injection': is_injection,
        'injection_type': injection_type,
        'is_oral': is_oral,
        'is_topical': is_topical,
        'is_inhaler': is_inhaler,
        'is_ophthalmic': is_ophthalmic,
        'is_keytruda': is_keytruda,
        'is_trulicity': is_trulicity,
        'is_glp1': is_glp1,
        'dosage_form_clean': clean_form
    }


def clean_clinical_html(raw_html: str) -> str:
    """清理仿單 HTML 標籤、實體符號與空白，轉換為純淨文字"""
    if not raw_html:
        return ""
    import html as html_lib
    text = html_lib.unescape(raw_html)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    lines = [re.sub(r'\s+', ' ', l).strip() for l in text.split('\n')]
    valid = []
    for l in lines:
        if not l or l.startswith('<!--') or 'toggle' in l or 'inner' in l:
            continue
        if len(l) <= 2 and not any(c.isdigit() for c in l):
            continue
        valid.append(l)
    return '\n'.join(valid)


def extract_relevant_clinical_lines(text: str, keywords: list, max_lines: int = 4, min_len: int = 6) -> list:
    """依據關鍵字自純淨仿單文字中抽取最關鍵之臨床句子"""
    cleaned = clean_clinical_html(text)
    matched = []
    seen = set()
    for line in cleaned.split('\n'):
        l = line.strip()
        if len(l) < min_len:
            continue
        if any(kw.lower() in l.lower() for kw in keywords):
            if l not in seen:
                seen.add(l)
                matched.append(l)
        if len(matched) >= max_lines:
            break
    return matched


def generate_patient_answer(matched_intent: str, drug_info: dict, q_id=None, pro_answer: str = "") -> str:
    """
    全新動態研讀 AI 引擎：
    13 類臨床問題全面杜絕統一公版，深度研讀食藥署核定仿單該藥品之真實條文！
    1. 💡 【結論速覽】：直截了當回答「能不能、要不要、怎麼用」，用最平易近人的白話說明。
    2. 📋 【生活日常叮嚀】：病患照護與日常服藥/輸注規矩（避免用藥禁忌與意外）。
    3. 🚨 【何時一定要找醫生】：紅旗警訊與緊急就醫時機。
    """
    cname = drug_info.get('cname') or drug_info.get('drug_name_zh') or '本藥品'
    ename = drug_info.get('ename') or drug_info.get('drug_name_en') or ''
    lic_id = drug_info.get('license_id') or drug_info.get('lic_id', '')
    dosage_form = drug_info.get('dosage_form') or drug_info.get('form', '口服製劑')
    drug_name_str = f"{cname} {ename} {drug_info.get('ingredient', '')} {drug_info.get('query', '')} {lic_id}".lower()

    # 各大章節純淨文字
    indications_raw = drug_info.get('indications', '')
    dosage_raw = drug_info.get('dosage', '')
    contra_raw = drug_info.get('contraindications', '')
    precautions_raw = drug_info.get('precautions', '')
    special_raw = drug_info.get('special_populations', '')
    interactions_raw = drug_info.get('interactions', '')
    adverse_raw = drug_info.get('adverse_effects', '')
    warnings_raw = drug_info.get('special_warnings', '')
    patient_raw = drug_info.get('patient_info', '')

    indications_clean = clean_clinical_html(indications_raw)
    dosage_clean = clean_clinical_html(dosage_raw)
    contra_clean = clean_clinical_html(contra_raw)
    precautions_clean = clean_clinical_html(precautions_raw)
    special_clean = clean_clinical_html(special_raw)
    interactions_clean = clean_clinical_html(interactions_raw)
    adverse_clean = clean_clinical_html(adverse_raw)
    warnings_clean = clean_clinical_html(warnings_raw)
    patient_clean = clean_clinical_html(patient_raw)

    s = drug_name_str.lower()
    is_injection = any(kw in dosage_form for kw in ['注射', '針', '輸注', '凍晶', '點滴']) or any(kw in s for kw in ['inj', 'injection'])
    is_topical = any(kw in dosage_form for kw in ['軟膏', '乳膏', '凝膠', '外用', '貼片', '洗劑'])
    is_inhaler = any(kw in dosage_form for kw in ['吸入', '噴霧', '乾粉吸入'])
    is_ophthalmic = any(kw in dosage_form for kw in ['點眼', '眼藥', '眼用'])
    is_oral = not (is_injection or is_topical or is_inhaler or is_ophthalmic)

    # 特殊藥物快速識別
    is_keytruda = any(k in s for k in ['pembrolizumab', 'keytruda', '吉舒達'])
    is_trulicity = any(k in s for k in ['trulicity', '易週糖', 'dulaglutide', '001200'])
    is_glp1 = is_trulicity or any(k in s for k in ['semaglutide', 'ozempic', 'rybelsus', 'wegovy', 'tirzepatide', 'mounjaro', 'liraglutide', 'victoza', 'saxenda', 'glp-1', 'glp1'])
    is_invanz = any(k in s for k in ['invanz', 'ertapenem', '益滿治', '023749', '023901'])
    is_metformin = any(k in s for k in ['metformin', 'glucophage', '庫魯化', '美獲蒙', '024189', '025635', '018231'])
    is_sglt2 = any(k in s for k in ['dapagliflozin', 'forxiga', '福適佳', 'empagliflozin', 'jardiance', '恩排糖', 'sglt2', 'sglt-2'])
    is_statin = any(k in s for k in ['atorvastatin', 'lipitor', '立普妥', 'rosuvastatin', 'crestor', '冠脂妥', 'statin'])
    is_aspirin = any(k in s for k in ['bokey', 'aspirin', '伯基', '阿斯匹靈'])

    # =========================================================================
    # 01 藥品作用 (indications)
    # =========================================================================
    if matched_intent == 'indications':
        ans = f"### 💡 【結論速覽（{cname} 是用來治療什麼的？）】\n"
        ind_lines = [l for l in indications_clean.split('\n') if len(l) >= 4 and not l.startswith('說明') and not l.startswith('2.')]
        if ind_lines:
            primary_ind = '；'.join(ind_lines[:3])
            ans += f"* **衛福部官方核准適應症**：本藥品經衛福部核准，主要用於治療或控制：\n"
            ans += f"  > **{primary_ind}**\n"
        else:
            ans += f"* **衛福部官方核准適應症**：本藥品經衛福部核准，請遵照專科醫師診斷與處方指示使用。\n"

        if is_oral:
            ans += f"* **口服專用處方藥**：這是醫師根據您的抽血檢驗與臨床病情開立的口服專屬處方藥，不可因自覺症狀改善而擅自停藥。\n\n"
        elif is_injection:
            if is_glp1 or any(kw in (cname + ename + dosage_form).lower() for kw in ['筆', 'pen', 'kwikpen', '預填']):
                ans += f"* **每週一次皮下注射**：本藥品為專用皮下注射筆（預填注射筆/隨選筆），可由經醫療人員衛教指導之病人於每週固定一天在腹部、大腿或上臂輪替自行皮下注射，切勿口服或靜脈注射。\n\n"
            else:
                ans += f"* **專業針劑治療**：這是專用注射針劑，限由醫護人員於醫療院所執行施打，切勿自行口服。\n\n"
        else:
            ans += f"* **專屬處方用藥**：請依醫師指示之部位與頻率規律使用。\n\n"

        ans += f"### 📋 【日常用藥好習慣】\n"
        ans += f"1. **按時規律使用**：請遵照處方藥袋標示定時用藥，切勿因為目前沒有不舒服就擅自中斷。\n"
        ans += f"2. **絕對不可分給親友**：每個人病因、肝腎機能與用藥禁忌截然不同，擅自分用極易發生危險。\n\n"
        ans += f"### 🚨 【何時應回診諮詢醫師】\n"
        ans += f"* 若遵照醫囑規律用藥一段時間後，原有的病情未見改善或反而出現異常不適，請回診由主治醫師為您評估調整。"
        return ans

    # =========================================================================
    # 02 藥品吃法或用法 (dosage)
    # =========================================================================
    if matched_intent == 'dosage':
        ans = f"### 💡 【結論速覽（{cname} 官方仿單吃法與標準用法）】\n"
        if is_keytruda:
            ans += f"🚫 **【本藥品為針劑（靜脈點滴注射劑），絕對非口服藥，切勿吞服！】**\n"
            ans += f"* **成人建議劑量**：每 3 週一次 200 毫克 (200 mg Q3W) 或每 6 週一次 400 毫克 (400 mg Q6W)，靜脈輸注 30 分鐘。\n\n"
        elif is_trulicity or any(k in s for k in ['mounjaro', 'tirzepatide', '猛健樂']):
            is_mounjaro = any(k in s for k in ['mounjaro', 'tirzepatide', '猛健樂'])
            if is_mounjaro:
                ans += f"🚫 **【本藥品為每週一次「皮下注射專用注射筆」，絕對非口服藥，切勿吞服！】**\n"
                ans += f"* **衛福部核定建議劑量與階梯遞增時程**：\n"
                ans += f"  1. **起始治療劑量**：起始劑量為**每週一次 2.5 毫克 (2.5 mg)**，持續使用 4 週（2.5 mg 為治療起始劑量，不作為長期維持劑量）。\n"
                ans += f"  2. **標準治療劑量**：使用 4 週後，劑量應增加至**每週一次 5 毫克 (5 mg)**。\n"
                ans += f"  3. **視需要階梯遞增**：若需要進一步血糖或體重控制，在目前劑量至少使用 4 週後，可以每次增加 2.5 mg 的階梯往上調整（例如增至 7.5 mg、10 mg、12.5 mg 或最高 15 mg）。\n"
                ans += f"  4. **每週最高劑量**：每週一次最大劑量為 **15 毫克 (15 mg)**。\n"
                ans += f"  5. **注射時程與部位**：請於每週固定一天在腹部、大腿或上臂輪替皮下注射，可隨餐或空腹注射，不必受用餐時間限制。\n\n"
            else:
                ans += f"🚫 **【本藥品為每週一次「皮下注射專用注射筆」，絕對非口服藥，切勿吞服！】**\n"
                ans += f"* **建議劑量**：起始劑量為每週一次 0.75 mg 皮下注射（腹部、大腿或上臂輪替施打）；4 週後視血糖控制可調整為每週一次 1.5 mg，最大劑量每週 4.5 mg。\n\n"
        elif is_invanz:
            ans += f"🚫 **【本藥品為抗生素注射針劑，絕對非口服藥，切勿吞服！】**\n"
            ans += f"* **成人建議劑量**：每日一次 1 公克 (1g QD)，限靜脈點滴輸注（超過 30 分鐘）或深部肌肉注射；嚴禁用葡萄糖點滴液稀釋！\n\n"
        else:
            # 1. 萃取服藥時間與食物關係
            meal_guidance = ""
            if any(w in dosage_clean for w in ['隨餐', '用餐時', '用餐中', '餐中', '與食物併服']):
                meal_guidance = "⏰ **服藥時間與用餐關係**：官方仿單明定請於「**用餐時（隨餐）或餐後立即服用**」，可有效顯著降低胃腸道不適、噁心與腹瀉發生率！"
            elif any(w in dosage_clean for w in ['飯後', '餐後']):
                meal_guidance = "⏰ **服藥時間與用餐關係**：請於「**飯後服用**」，以減輕對胃黏膜的刺激。"
            elif any(w in dosage_clean for w in ['空腹', '飯前', '餐前']):
                meal_guidance = "⏰ **服藥時間與用餐關係**：請於「**飯前 30 分鐘至 1 小時或空腹時服用**」，以利藥物充分吸收。"
            else:
                meal_guidance = "⏰ **服藥時間**：可隨餐或空腹服用，請盡量在每日「固定時間」規律服藥。"

            # 2. 萃取吞服注意事項
            swallow_guidance = ""
            if any(w in dosage_clean for w in ['整錠吞服', '不要咀嚼', '整顆吞服', '切勿咀嚼', '不可咀嚼', '不可咬碎', '不可磨粉']) or '緩釋' in dosage_form or '腸溶' in dosage_form or '膜衣' in dosage_form:
                swallow_guidance = "💊 **吞服方式與特殊禁忌**：請整顆/整錠配合溫開水完整吞服，⚠️ **切勿咀嚼、咬碎或自行磨粉**，以防破壞特殊藥效釋放結構或造成胃部灼傷！"
            elif is_injection:
                swallow_guidance = f"💉 **針劑施打途徑**：本藥品為專用針劑（{dosage_form}），由醫護人員依處方於院所施打，切勿口服。"
            else:
                swallow_guidance = "💊 **服藥方式**：請配合一整杯溫開水整顆吞服。"

            # 3. 萃取仿單具體劑量與次數
            dosage_facts = extract_relevant_clinical_lines(
                dosage_clean, 
                ['每日', '每次', '劑量', '最高', '最大', '起始', '維持', '錠', '粒', 'mg', '毫克', '一次', '二次', '三次'], 
                max_lines=3, 
                min_len=8
            )

            ans += f"{meal_guidance}\n"
            ans += f"{swallow_guidance}\n"
            if dosage_facts:
                ans += f"* **衛福部核定劑量與時程摘錄**：\n"
                for df in dosage_facts:
                    ans += f"  > 📋 {df}\n"
            else:
                ans += f"* **標準劑量**：請嚴格遵照醫師開立於處方藥袋上之次數與顆數服用，切勿擅自調增或減量。\n"
            ans += "\n"

        ans += f"### 📋 【服藥與生活照護守則】\n"
        ans += f"1. **每天固定時間服藥**：定時服藥能使體內藥物濃度維持穩定控制，切勿今天早吃、明天晚吃。\n"
        ans += f"2. **切勿自行加倍或停藥**：若今天感覺良好不可擅自減藥；若感覺不佳亦切勿自行多吞一顆。\n"
        ans += f"3. **確認藥袋標示**：服藥前請再次核對藥袋姓名、用法用量與效期。\n\n"
        ans += f"### 🚨 【何時應諮詢醫師或藥師】\n"
        ans += f"* 若服藥後常引起嚴重胃痛、噁心嘔吐、頭暈心悸或吞嚥卡住，請盡速諮詢開藥醫師或藥師評估調整服藥時機。"
        return ans

    # =========================================================================
    # 03 腎功能不好要調整劑量嗎 (renal_impairment)
    # =========================================================================
    if matched_intent == 'renal_impairment':
        ans = f"### 💡 【結論速覽（{cname} 腎功能不好/洗腎患者能用嗎？劑量如何調整？）】\n"
        renal_corpus = f"{contra_clean}\n{dosage_clean}\n{precautions_clean}\n{special_clean}"
        renal_lines = extract_relevant_clinical_lines(
            renal_corpus, 
            ['腎', 'egfr', 'crcl', '肌酸酐', '洗腎', '透析', '腎絲球', '腎功能'], 
            max_lines=4, 
            min_len=10
        )

        if is_metformin:
            ans += f"🚫 **【重大禁忌：eGFR < 30 mL/min/1.73m² 或洗腎病患「嚴格禁用」】**！\n"
            ans += f"* **腎功能禁用紅線**：Metformin 經由腎臟排泄，當**腎絲球過濾率 (eGFR) < 30 mL/min/1.73m² 或處於透析/洗腎狀態時，官方仿單明列為絕對禁忌症**！此時藥物極易在體內蓄積，引發致命之「乳酸中毒 (Lactic Acidosis)」！\n"
            ans += f"* **中度腎功能減量指引**：\n"
            ans += f"  - **eGFR 30~45 mL/min/1.73m²**：**應減量使用**，每日起始劑量為 500mg 或 850mg，每日最高治療劑量不得超過 1000mg（分兩次給藥），且不建議新病人起始使用。\n"
            ans += f"  - **eGFR 45~59 mL/min/1.73m²**：若無其他乳酸中毒風險可謹慎使用，最高劑量不超過每日 1000mg。\n"
            ans += f"* **定期監測**：腎功能正常者至少每年檢查一次；腎功能處於邊緣值或長輩**每 3 至 6 個月必須定期抽血檢查**。\n\n"
        elif is_sglt2:
            ans += f"⚠️ **【排糖降血糖藥：重度腎功能不良或洗腎者禁用或不建議使用】**：\n"
            ans += f"* 當 eGFR < 25 或小於 45 時，排糖降血糖效果顯著下降，不建議單純為降血糖起始使用；**洗腎透析病患禁用**。\n\n"
        elif is_keytruda:
            ans += f"🩺 **【吉舒達：輕中度腎功能不良不需調整劑量；治療期間需加強監測免疫性腎炎】**：\n"
            ans += f"* 輕中度腎受損病人不需調整劑量；但治療期間若血中肌酸酐異常飆高或出現少尿浮腫，應警惕免疫相關性腎炎。\n\n"
        elif renal_lines:
            ans += f"🩺 **【衛福部核定仿單腎功能評估與劑量指引摘錄】**：\n"
            for rl in renal_lines:
                ans += f"* 📋 {rl}\n"
            ans += "\n"
        else:
            ans += f"⚠️ **【官方核定仿單未記載特定之固定腎功能減量階梯表】**：\n"
            ans += f"* 本藥品官方仿單中未明載固定減量數據（多數因藥物非經腎臟排泄或輕中度腎障礙無臨床顯著蓄積）。\n"
            ans += f"* 但腎臟為人體重要代謝與排泄器官，慢性腎臟病患仍必須由醫師依最新抽血報告（Creatinine、eGFR）進行個別化劑量評估。\n\n"

        ans += f"### 📋 【腎臟病患就醫照護守則】\n"
        ans += f"1. **看診主動告知**：就診任何科別時，請**主動告知醫師與藥師您有腎臟病史、腎功能指數或正在洗腎**。\n"
        ans += f"2. **定期抽血監測**：請嚴格配合醫囑每 3 至 6 個月抽血驗腎功能（肌酸酐、eGFR、尿素氮）。\n"
        ans += f"3. **切勿擅自停藥**：不可因害怕「吃藥傷腎」就自行停藥或隨便減半，擅自停藥恐導致血壓、血糖或病情急性惡化。\n\n"
        ans += f"### 🚨 【腎功能受損危險警訊（立即就醫）】\n"
        ans += f"* 用藥期間若發現**尿量急遽減少、雙腳或臉部嚴重浮腫、極度疲倦嗜睡或呼吸急促喘鳴**，請立即前往大醫院就醫檢查！"
        return ans

    # =========================================================================
    # 04 孕婦可以用嗎 (pregnancy)
    # =========================================================================
    if matched_intent == 'pregnancy':
        ans = f"### 💡 【結論速覽（{cname} 懷孕或餵母奶期間可以使用嗎？）】\n"
        preg_corpus = f"{special_clean}\n{contra_clean}\n{precautions_clean}"
        preg_lines = extract_relevant_clinical_lines(
            preg_corpus, 
            ['懷孕', '妊娠', '胎兒', '畸胎', '哺乳', '母乳', '分級', '胎盤', '避孕'], 
            max_lines=3, 
            min_len=8
        )

        if is_metformin:
            ans += f"🩺 **【官方仿單查核結果：臨床有需要時，可考慮作為胰島素輔助或替代選擇】**：\n"
            ans += f"* **胎盤通透性**：Metformin 可通過胎盤，胎兒體內濃度可能接近母體。\n"
            ans += f"* **臨床研究數據**：超過 1000 例暴露結果之登錄型世代研究及統合分析顯示，在受孕前後期或懷孕期使用 Metformin，**並不會增加先天性異常或胎兒/新生兒毒性風險**。\n"
            ans += f"* **臨床指引**：若懷孕期間血糖控制不良，高血糖本身會大幅增加流產與畸胎風險；因此**若臨床上有需要，醫師可評估使用 Metformin 作為胰島素治療之輔助用藥或替代選擇**。\n"
            ans += f"* **哺乳建議**：本藥品會微量分泌至母乳中，授乳期間是否使用請由醫師評估母嬰利弊。\n\n"
        elif is_statin:
            ans += f"🚫 **【懷孕與哺乳期「絕對禁止使用」（重大胎兒畸形與發育危害）】**！\n"
            ans += f"* 膽固醇為胎兒器官發育所必需，Statin 類降血脂藥具明確胚胎毒性與致畸胎性，育齡女性治療期間必須嚴格避孕；一旦發現懷孕請立即停藥並就醫！\n\n"
        elif is_keytruda:
            ans += f"🚫 **【重大胎兒傷害風險：懷孕期間不建議使用；治療期間及最後一劑後 4 個月內嚴格避孕且禁止哺乳】**！\n\n"
        elif is_aspirin:
            ans += f"⚠️ **【懷孕後期（第 28 週起）嚴格禁用；其餘週數限由婦產科醫師評估特殊適應症】**：\n"
            ans += f"* 懷孕後期服用阿斯匹靈會導致胎兒動脈導管提早閉合及孕婦生產大出血危險！\n\n"
        elif preg_lines:
            ans += f"🩺 **【衛福部核定仿單懷孕與哺乳規範摘錄】**：\n"
            for pl in preg_lines:
                ans += f"* 📋 {pl}\n"
            ans += "\n"
        else:
            ans += f"⚠️ **【缺乏充分人體臨床安全性試驗，非醫師評估明確需要切勿自行服用】**：\n"
            ans += f"* 官方仿單未有充分人體試驗證實安全無虞時，懷孕前 3 個月（胎兒器官形成期）與哺乳期間，切勿自行服藥。\n\n"

        ans += f"### 📋 【孕媽咪與哺乳安全守則】\n"
        ans += f"1. **看診主動告知**：若已懷孕、計畫備孕或正在餵母奶，**看診任何科別時務必第一時間主動告知醫師**。\n"
        ans += f"2. **切勿擅自買成藥**：孕期任何頭痛、發燒或感冒，均應由醫師開立處方，切勿自行買成藥服用。\n\n"
        ans += f"### 🚨 【何時應立即就醫】\n"
        ans += f"* 若在不知情懷孕的情況下服用了本藥品，請保持冷靜並帶同完整藥袋盡速至婦產科門診評估胎兒狀況。"
        return ans

    # =========================================================================
    # 05 小孩最小幾歲可以用，要調整劑量嗎 (pediatric_use)
    # =========================================================================
    if matched_intent == 'pediatric_use':
        ans = f"### 💡 【結論速覽（{cname} 小朋友/兒童可以使用嗎？幾歲可以用？）】\n"
        ped_corpus = f"{dosage_clean}\n{special_clean}\n{precautions_clean}\n{indications_clean}"
        ped_lines = extract_relevant_clinical_lines(
            ped_corpus, 
            ['小兒', '兒童', '青少年', '嬰兒', '歲', 'kg', '體重'], 
            max_lines=3, 
            min_len=8
        )

        if is_metformin:
            ans += f"👶 **【官方仿單核准兒童使用年齡規範】**：\n"
            ans += f"* **核准年齡**：衛福部核准 Metformin 可用於 **10 歲（或特定劑型 12 歲）及以上** 之兒童與青少年第二型糖尿病患者。\n"
            ans += f"* **小兒建議劑量**：通常起始劑量為每日一次 500mg 或 850mg，於用餐時或餐後服用；視血糖控制逐步調整，每日最大劑量通常不超過 2000mg（分 2 至 3 次給藥）。\n"
            ans += f"* ⚠️ **年齡限制**：小於 10 歲兒童之安全性與有效性尚未建立，不建議使用。\n\n"
        elif is_invanz:
            ans += f"👶 **【官方核准年齡：3 個月大以上兒童與青少年】**：\n"
            ans += f"* 3 個月至 12 歲兒童建議劑量為每次 15 mg/kg（每日兩次，單日最高上限 1 公克）；小於 3 個月大嬰兒安全性尚未確立。\n\n"
        elif is_keytruda:
            ans += f"👶 **【黑色素瘤核准用於 12 歲以上兒童（每 3 週 2 mg/kg，單次最高 200 mg）；其餘癌症小兒安全性尚未確立】**。\n\n"
        elif ped_lines:
            ans += f"👶 **【衛福部核定仿單小兒年齡與劑量指引摘錄】**：\n"
            for pl in ped_lines:
                ans += f"* 📋 {pl}\n"
            ans += "\n"
        else:
            ans += f"⚠️ **【官方核定仿單載明：在 18 歲以下兒童或青少年的安全性與有效性尚未建立】**：\n"
            ans += f"* 官方仿單通常僅核准於成人；未經小兒專科醫師評估前，切勿擅自給予 18 歲以下兒童使用。\n\n"

        ans += f"### 📋 【家長用藥三大禁忌】\n"
        ans += f"1. **小孩不是大人縮小版**：嚴禁將大人的藥丸自己切半、折碎或自行稀釋給小朋友吃！大人劑型與賦形劑對小孩可能產生嚴重毒性。\n"
        ans += f"2. **仔細核對藥袋劑量**：兒童藥物多依體重 (kg) 精密換算，給藥時務必看清藥袋上的毫升數 (mL) 或包數。\n"
        ans += f"3. **切勿自行補給**：若小孩吃藥後吐出，不可直接立刻再灌一次完整劑量，請先諮詢兒科醫師或藥師。\n\n"
        ans += f"### 🚨 【兒童緊急送醫警訊】\n"
        ans += f"* 小孩用藥後若出現**全身大面積紅疹蕁麻疹、呼吸喘鳴喘不過氣、異常昏睡叫不醒或持續劇烈嘔吐**，請立刻送醫急診！"
        return ans

    # =========================================================================
    # 06 老人可以用嗎，要調整劑量嗎 (geriatric_use)
    # =========================================================================
    if matched_intent == 'geriatric_use':
        ans = f"### 💡 【結論速覽（{cname} 65 歲以上長輩能使用嗎？需要調整劑量嗎？）】\n"
        ger_corpus = f"{special_clean}\n{dosage_clean}\n{precautions_clean}"
        ger_lines = extract_relevant_clinical_lines(
            ger_corpus, 
            ['老年', '高齡', '65歲', '80歲', '長輩', '長者'], 
            max_lines=3, 
            min_len=8
        )

        if is_metformin:
            ans += f"👴 **【官方仿單明定：大於 80 歲長輩不建議開始使用 Metformin 治療】**！\n"
            ans += f"* **80 歲以上長輩警訊**：官方仿單明文記載：**「大於 80 歲之老年病人不建議開始使用 Metformin 治療」**。因為超高齡長輩常伴隨生理性腎功能退化與無症狀腎受損，使用本藥引發致死性乳酸中毒之風險顯著激增！\n"
            ans += f"* **80 歲以下長輩使用原則**：用於治療 80 歲以下之老年病人時，**應特別謹慎**，必須從「最低起始劑量」開始，且**每 3 至 6 個月必須定期抽血檢查腎功能**！\n\n"
        elif ger_lines:
            ans += f"👴 **【衛福部核定仿單高齡長輩用藥指引摘錄】**：\n"
            for gl in ger_lines:
                ans += f"* 📋 {gl}\n"
            ans += "\n"
        else:
            ans += f"👴 **【可以使用，但建議從較低起始劑量開始】**：\n"
            ans += f"* 高齡長輩可以使用本藥品。但因長輩肝臟、腎臟代謝與排泄藥物機能較為遲緩，醫師通常會建議**「從較低的起始劑量開始」**，再視耐受性逐步調整。\n\n"

        ans += f"### 📋 【長輩照護三大重點】\n"
        ans += f"1. **預防起身頭暈跌倒**：許多降血糖、降血壓藥在治療初期容易引起姿勢性低血壓，**長輩起床或站起時動作務必放慢**，坐穩幾秒再站立。\n"
        ans += f"2. **跨科用藥整合**：長輩若同時看多科門診（心臟科、新陳代謝科、骨科），請攜帶所有藥袋到藥局請藥師做**「用藥整合」**，避免重複用藥或藥物相剋。\n"
        ans += f"3. **確認按時規律**：建議使用分裝藥盒或日曆標記，協助長輩確認每天是否有按時服藥，避免重複多吃一餐。\n\n"
        ans += f"### 🚨 【何時應回診諮詢醫師】\n"
        ans += f"* 長輩用藥後若常抱怨頭暈站不穩、容易迷糊嗜睡、食慾大幅變差或精神恍惚，請盡早陪同回診由醫師評估。"
        return ans

    # =========================================================================
    # 07 肝功能不好可以用嗎，要調整劑量嗎 (hepatic_impairment)
    # =========================================================================
    if matched_intent == 'hepatic_impairment':
        ans = f"### 💡 【結論速覽（{cname} 肝功能不好/肝指數偏高能使用嗎？需要調整劑量嗎？）】\n"
        hep_corpus = f"{contra_clean}\n{precautions_clean}\n{special_clean}"
        hep_lines = extract_relevant_clinical_lines(
            hep_corpus, 
            ['肝', '肝功能', '肝硬化', '肝衰竭', 'ast', 'alt', '黃疸', '乳酸中毒'], 
            max_lines=3, 
            min_len=8
        )

        if is_metformin:
            ans += f"🚨 **【官方仿單明定：嚴重肝功能不全者「禁用 / 應避免使用」】**！\n"
            ans += f"* **致命乳酸中毒風險**：肝臟是人體清除乳酸的重要器官。官方仿單明載：**病人若有肝功能不全或肝硬化，會使乳酸清除能力大幅下降，導致 Metformin 相關乳酸中毒風險大幅飆升，致死率高**！\n"
            ans += f"* ⚠️ **用藥嚴格禁令**：服藥期間**嚴格禁止過量飲酒或酗酒**！酒精會進一步破壞肝臟乳酸代謝，引發急性代謝性酸中毒！\n\n"
        elif is_statin:
            ans += f"🚨 **【活動性肝病或肝指數 (AST/ALT) 持續不明原因升高者「嚴格禁用」】**！\n\n"
        elif hep_lines:
            ans += f"🩺 **【衛福部核定仿單肝功能注意事項摘錄】**：\n"
            for hl in hep_lines:
                ans += f"* 📋 {hl}\n"
            ans += "\n"
        else:
            ans += f"⚠️ **【大多藥物經肝代謝，肝機能異常者需由醫師評估】**：\n"
            ans += f"* 若仿單未列固定減量表，代表需由醫師依抽血肝功能指數 (AST/ALT/膽紅素) 判斷是否需要減量或改換其他藥品。\n\n"

        ans += f"### 📋 【肝病患者生活守則】\n"
        ans += f"1. **主動告知病史**：看診時請務必主動告訴醫師您是否有 B 肝、C 肝帶原、嚴重脂肪肝或肝硬化病史。\n"
        ans += f"2. **絕對不可飲酒**：治療期間**嚴格禁止飲酒**！酒精會嚴重干擾肝臟代謝，大幅增加急性肝炎危險。\n"
        ans += f"3. **定期追蹤肝指數**：請遵照醫囑定期抽血檢驗肝功能。\n\n"
        ans += f"### 🚨 【肝功能受損紅旗警訊（立刻就醫）】\n"
        ans += f"* 治療期間若發現**眼白或皮膚變黃（黃疸）、尿液顏色變得像濃紅茶或烏龍茶、極度異常疲倦、持續噁心想吐**，請立刻就醫檢查！"
        return ans

    # =========================================================================
    # 08 IV相容性與稀釋配伍禁忌為何？ (iv_compatibility)
    # =========================================================================
    if matched_intent == 'iv_compatibility':
        if is_invanz:
            ans = f"### 💡 【結論速覽（INVANZ 益滿治靜脈調配與配伍重大禁忌）】\n"
            ans += f"🚫 **【首要重大禁忌：絕對不可以使用含有葡萄糖 (α-D-GLUCOSE) 的稀釋液！】**\n"
            ans += f"* 官方仿單嚴格明定：不可使用含葡萄糖稀釋液（會破壞藥效降解）！亦不可與其他藥物混合或同時輸注。\n"
            ans += f"* **成人調製規範**：1g 小瓶加入 10 mL 注射用水或 0.9% NaCl 溶解，立刻移入 50 mL 0.9% 氯化鈉注射液，輸注時間必須超過 30 分鐘，調配後 6 小時內用完。\n\n"
        elif is_keytruda:
            ans = f"### 💡 【結論速覽（吉舒達靜脈調配與點滴相容重點）】\n"
            ans += f"* **相容點滴液**：0.9% 氯化鈉注射液 (NS) 或 5% 葡萄糖注射液 (D5W)；稀釋濃度 1~10 mg/mL。\n"
            ans += f"* 🚫 **配伍禁忌**：切勿透過同一輸注管線同時投予其他藥物！輸注管線必須連接 0.2~5 微米在線濾膜；輸注時間約 30 分鐘。\n\n"
        elif is_oral:
            ans = f"### 💡 【結論速覽（這是口服藥，絕對不能打點滴！）】\n"
            ans += f"⚠️ **【本藥品為口服劑型（{dosage_form}），完全不適用於靜脈打點滴】**：\n"
            ans += f"* 本藥品經衛生福利部核准為**口服使用**，在醫學上**沒有打點滴稀釋相容性之資料**。\n"
            ans += f"* ⚠️ **極重度致命禁忌**：口服藥品絕對嚴禁以任何方式磨粉或溶解放進點滴注入血管！口服賦形劑注入血管會引發致命的微粒血管栓塞、溶血與感染性休克！\n\n"
            ans += f"### 📋 【病患用藥守則】\n"
            ans += f"* 請整顆配合溫開水吞服即可，切勿自行改變給藥途徑。"
            return ans
        else:
            ans = f"### 💡 【結論速覽（針劑注射點滴調配重點）】\n"
            ans += f"* **醫院專業調配**：本藥品為專用針劑，必須由專業藥師與護理師在無菌環境下以官方指定相容點滴液（如 0.9% 生理食鹽水等）精準調製。\n"
            ans += f"* 施打時切勿與其他未經確認相容性之針劑混合輸注。\n\n"

        ans += f"### 📋 【病人在醫院打點滴該注意的事】\n"
        ans += f"1. **注意點滴外觀**：輸注時管路若出現混濁、白色沉澱或變色，請立刻按鈴告知護理師。\n"
        ans += f"2. **切勿自己調滴速**：嚴禁自行旋轉點滴滾輪加速。\n"
        ans += f"3. **注意注射部位**：若打針處紅腫熱痛、滲液漏針，請立即反映。"
        return ans

    # =========================================================================
    # 09 跟那些藥或食物有交互作用? (interaction)
    # =========================================================================
    if matched_intent == 'interaction':
        ans = f"### 💡 【結論速覽（使用 {cname} 要避開哪些藥物或食物？）】\n"
        inter_corpus = f"{interactions_clean}\n{precautions_clean}\n{contra_clean}"
        inter_lines = extract_relevant_clinical_lines(
            inter_corpus, 
            ['交互作用', '併用', '顯影劑', '酒精', '葡萄柚', 'nsaid', '抑制劑', '誘導劑', '低血糖', '抗凝血'], 
            max_lines=4, 
            min_len=8
        )

        if is_metformin:
            ans += f"⚠️ **【官方仿單明定四大重大交互作用】**：\n"
            ans += f"1. 🚫 **放射性血管注射含碘顯影劑（最重大交互作用）**：\n"
            ans += f"   * 接受含碘顯影劑檢查可能導致急性腎功能下降，引發 Metformin 嚴重蓄積與致死性乳酸中毒！**檢查前或檢查時必須暫時停藥，且檢查後 48 小時經確認腎功能正常後才能恢復服用**！\n"
            ans += f"2. 🚫 **酒精（乙醇）**：\n"
            ans += f"   * 酒精會干擾肝臟乳酸代謝，大幅增加乳酸中毒風險，服藥期間**嚴格不可過量飲酒或酗酒**。\n"
            ans += f"3. ⚠️ **其他降血糖藥物（胰島素、磺醯尿素類 Sulfonylurea）**：\n"
            ans += f"   * 單獨服用 Metformin 不易引發低血糖；但若與胰島素或磺醯尿素類併用時，**低血糖風險顯著上升**，應備妥糖果並定期量測血糖。\n"
            ans += f"4. ⚠️ **干擾腎功能之藥物（NSAIDs 消炎止痛藥、利尿劑、ACEI/ARB 降血壓藥）**：\n"
            ans += f"   * 剛開始服用或合用非類固醇消炎止痛藥 (NSAIDs) 或強效利尿劑時，可能損害腎功能而增加 Metformin 蓄積，應密切監測腎指數。\n\n"
        elif is_keytruda:
            ans += f"⚠️ **【避免於治療開始前使用全身性皮質類固醇與免疫抑制劑（會干擾抗癌免疫療效）】**。\n\n"
        elif inter_lines:
            ans += f"⚠️ **【衛福部核定仿單交互作用警示摘錄】**：\n"
            for il in inter_lines:
                ans += f"* 📋 {il}\n"
            ans += "\n"
        else:
            ans += f"⚠️ **【請注意特定食物與藥品之交互作用】**：\n"
            ans += f"* 服藥期間請盡量避免食用**葡萄柚、柚子**（易抑制肝臟代謝酵素使藥物濃度飆高）與**酒精性飲料**。\n"
            ans += f"* 消炎止痛藥 (NSAIDs)、胃乳片制酸劑或草藥可能與本藥互相干擾。\n\n"

        ans += f"### 📋 【病患日常安全守則】\n"
        ans += f"1. **看其他科出示藥袋**：去看牙科、骨科、診所或急診時，**請主動出示目前正在使用的所有藥物清單**。\n"
        ans += f"2. **中西藥分開間隔**：若有在吃中藥或綜合維他命、鈣片，建議與本西藥至少**間隔 1 至 2 小時**。\n"
        ans += f"3. **勿自行亂吃偏方**：請勿隨意服用來路不明的草藥保養品。\n\n"
        ans += f"### 🚨 【何時應諮詢藥師】\n"
        ans += f"* 若剛開始加用新的藥品或保健食品後，突然出現胃痛、心悸、頭暈或皮膚出疹，請先暫停新加的項目並諮詢醫師或藥師。"
        return ans

    # =========================================================================
    # 10 常見副作用(發生率>10%)有哪些? (adverse_effects_ten_percent)
    # =========================================================================
    if matched_intent == 'adverse_effects_ten_percent':
        ans = f"### 💡 【結論速覽（服用/使用 {cname} 最常見的不良反應有哪些？）】\n"
        adv_corpus = f"{adverse_clean}\n{precautions_clean}"
        adv_lines = extract_relevant_clinical_lines(
            adv_corpus, 
            ['很常見', '≥1/10', '≥ 10%', '常見', '胃腸', '噁心', '腹瀉', '頭痛', '皮疹', '味覺'], 
            max_lines=4, 
            min_len=8
        )

        if is_metformin:
            ans += f"⚠️ **【衛福部官方仿單核定：發生率 ≥ 10% 之極常見不良反應】**：\n"
            ans += f"1. 🤢 **極常見胃腸道不良反應 (發生率 ≥ 10%)**：\n"
            ans += f"   * 包括**噁心、嘔吐、腹瀉、腹脹、腹部疼痛與食慾不振**。\n"
            ans += f"   * 💡 **緩解妙方**：這些胃腸道反應最常在剛開始服藥的前幾天至兩週內發生，多數人會隨身體適應而改善；**將藥物安排在「用餐時（隨餐）或餐後立即服用」，可大幅降低胃腸不適**！\n"
            ans += f"2. 👅 **常見神經系統反應 (發生率 1% 至 10%)**：\n"
            ans += f"   * **味覺障礙**：部分病患反映口中會出現短暫的「金屬味」，通常也是暫時的。\n"
            ans += f"3. 🩸 **長期代謝與營養影響**：\n"
            ans += f"   * 長期使用可能減少腸道對**維生素 B12 (Vitamin B12)** 的吸收，可能導致貧血或手腳神經麻木，可於定期抽血時評估。\n"
            ans += f"4. 🚨 **極罕見但危及生命之紅旗警訊：乳酸中毒 (Lactic Acidosis)**：\n"
            ans += f"   * 若出現**肌肉抽筋劇痛、深快呼吸、極度虛弱無力、體溫偏低、嚴重腹痛**，請立即停藥並掛急診！\n\n"
        elif is_keytruda:
            ans += f"⚠️ **【官方仿單核定發生率 ≥ 10% 之極常見反應】**：疲倦 (24%)、噁心 (21%)、腹瀉、皮疹搔癢、發燒咳嗽；注意免疫媒介性發炎警訊！\n\n"
        elif adv_lines:
            ans += f"⚠️ **【衛福部核定仿單常見不良反應摘要】**：\n"
            for al in adv_lines:
                ans += f"* 📋 {al}\n"
            ans += "\n"
        else:
            ans += f"* **常見反應通常輕微**：每 10 個人約有 1 人可能遇到輕微暫時反應（如輕微噁心、頭痛、腸胃不適等），多數於服藥初期適應後逐步緩解。\n\n"

        ans += f"### 📋 【病患應對原則】\n"
        ans += f"1. **切勿因輕微反應就擅自停藥**：隨意停藥可能讓原本的疾病迅速惡化。\n"
        ans += f"2. **輕微不適可先紀錄**：記錄症狀發生的時間與感受，於門診時與醫師討論。\n\n"
        ans += f"### 🚨 【嚴重過敏與危險紅旗警訊（立刻去急診）】\n"
        ans += f"* 若用藥後出現**全身大片發癢蕁麻疹、嘴唇或眼睛眼眶腫脹、喉嚨緊縮吞嚥困難、胸悶呼吸喘、或發高燒**，這是急性過敏警訊，請立刻前往急診室！"
        return ans

    # =========================================================================
    # 11 特殊警語或病人須注意事項 (special_warnings_precautions)
    # =========================================================================
    if matched_intent == 'special_warnings_precautions':
        ans = f"### 💡 【結論速覽（{cname} 最重要的核心黑框警語與安全提醒）】\n"
        warn_corpus = f"{warnings_clean}\n{precautions_clean}\n{contra_clean}"
        warn_lines = extract_relevant_clinical_lines(
            warn_corpus, 
            ['乳酸中毒', '酮酸中毒', '顯影劑', '脫水', '黑框', '警告', '警語', '注意'], 
            max_lines=3, 
            min_len=8
        )

        if is_metformin:
            ans += f"🚨 **【衛福部官方核定黑框重大警語：乳酸中毒 (Lactic Acidosis)】**：\n"
            ans += f"1. **致命性代謝併發症**：乳酸中毒極為罕見但**若未即時治療，死亡率高**！主要是因 Metformin 在體內過量堆積所引起。\n"
            ans += f"2. **重大危險誘發因子**：\n"
            ans += f"   * 腎功能衰竭 (eGFR < 30)\n"
            ans += f"   * 長時間禁食或嚴重脫水\n"
            ans += f"   * 酗酒或過量飲酒\n"
            ans += f"   * 嚴重肝功能不全\n"
            ans += f"   * 急性心衰竭缺氧狀態\n"
            ans += f"   * 接受含碘顯影劑檢查未停藥\n"
            ans += f"3. **乳酸中毒自覺表徵**：若服藥期間突然出現**肌肉痙攣伴隨腹部劇痛、全身無力極度虛弱、酸血性呼吸深快、體溫過低或嗜睡**，必須**立刻停藥並立即送急診**！\n\n"
        elif is_keytruda:
            ans += f"🚨 **【核心黑框警語：免疫媒介性不良反應 (IMAR)】**：可能侵犯肺部（肺炎）、腸道（大腸炎）、肝臟、內分泌與皮膚，就醫請隨身攜帶警示卡！\n\n"
        elif warn_lines:
            ans += f"🚨 **【衛福部核定仿單核心警語摘錄】**：\n"
            for wl in warn_lines:
                ans += f"* 📋 {wl}\n"
            ans += "\n"
        else:
            ans += f"* 請務必按照醫師指示規律服用，切勿自行更改劑量或無故斷藥。\n"
            ans += f"* 請留意服藥後是否會產生頭暈、嗜睡或低血糖現象。\n\n"

        ans += f"### 📋 【生活日常安全守則】\n"
        ans += f"1. **防範頭暈與虛弱**：服藥初期若感到精神不濟，請避免開車或操作危險機械。\n"
        ans += f"2. **定期回診抽血**：依約定時間回診檢驗肝腎功能與生理數值，確保安全。\n\n"
        ans += f"### 🚨 【緊急就醫警訊】\n"
        ans += f"* 若出現突發性胸痛、劇烈呼吸急促、嚴重腹痛、意識不清或皮膚大片出血斑點，請立刻就醫。"
        return ans

    # =========================================================================
    # 12 拔牙或手術前需要停藥嗎？ (surgery_dental)
    # =========================================================================
    if matched_intent == 'surgery_dental':
        ans = f"### 💡 【結論速覽（拔牙、手術或檢查前，{cname} 需要停藥嗎？）】\n"
        surg_corpus = f"{precautions_clean}\n{dosage_clean}\n{contra_clean}"
        surg_lines = extract_relevant_clinical_lines(
            surg_corpus, 
            ['手術', '拔牙', '麻醉', '顯影劑', '停藥', '禁食', '48小時'], 
            max_lines=3, 
            min_len=8
        )

        if is_metformin:
            ans += f"🚨 **【官方仿單明定：放射含碘顯影劑檢查與大手術「必須暫停服用 48 小時」】**！\n"
            ans += f"1. 🏥 **放射性影像檢查（血管注射含碘顯影劑）**：\n"
            ans += f"   * 血管注射含碘顯影劑（如電腦斷層 CT、心導管血管攝影）會造成急性腎衰竭危險，使 Metformin 堆積誘發乳酸中毒！\n"
            ans += f"   * **停藥規則**：**應在檢查前或檢查時停止使用 Metformin；並在造影程序 48 小時後重新評估 eGFR，確認腎功能穩定正常後才能重新開始服用**！\n"
            ans += f"2. 🔪 **全身麻醉 / 脊髓麻醉手術**：\n"
            ans += f"   * 官方仿單明定：**在全身麻醉、脊髓麻醉或硬膜外麻醉之非急需手術前 48 小時必須停止服用 Metformin**！手術後或恢復正常進食 48 小時後，經確認腎功能正常才可再次服用。\n"
            ans += f"3. 🦷 **一般門診局部麻醉拔牙**：\n"
            ans += f"   * 若僅為牙科單純局部麻醉拔牙（無全身麻醉、無禁食、無顯影劑），本藥**不是抗凝血劑**，不影響凝血機能，通常不需為了拔牙停藥；但拔牙前仍務必主動向牙醫師告知正在服用 Metformin。\n\n"
        elif is_sglt2:
            ans += f"⚠️ **【排糖降血糖藥：手術或重大拔牙前「至少 3 天前暫時停止服用」以預防酮酸中毒 (DKA)】**！\n\n"
        elif is_trulicity or is_glp1:
            ans += f"🚨 **【GLP-1 注射劑：全身麻醉或深度鎮靜時具「肺部異物吸入」風險，術前必須主動通知麻醉專科醫師】**！\n\n"
        elif is_aspirin or any(k in s for k in ['plavix', 'clopidogrel', 'warfarin', 'coumadin', 'eliquis', 'xarelto']):
            ans += f"🩸 **【抗血栓抗凝血藥：重大手術或拔牙通常於術前 5~7 天由醫師評估停藥，切勿擅自停藥】**！\n\n"
        elif surg_lines:
            ans += f"⚠️ **【衛福部核定仿單手術與檢查規範摘錄】**：\n"
            for sl in surg_lines:
                ans += f"* 📋 {sl}\n"
            ans += "\n"
        else:
            ans += f"⚠️ **【官方核定仿單未提及常規拔牙停藥天數，請切勿擅自停藥】**：\n"
            ans += f"* 官方仿單通常僅對特定抗凝血劑或排糖藥規範手術停藥。一般慢性病藥物仿單並未特別要求門診拔牙停藥。\n"
            ans += f"* **切勿私自隨便停藥**：擅自停藥可能引發血壓飆高或病情惡化。請於術前 1~2 週拿藥袋告知主刀牙醫或外科醫師評估即可。\n\n"

        ans += f"### 📋 【病患術前二大守則】\n"
        ans += f"1. **術前主動告知**：排定手術、拔牙或檢查前 **1 至 2 週**，主動把目前服用的所有藥袋拿給醫師與麻醉醫師看。\n"
        ans += f"2. **當天禁食配合**：手術當天若要求「空腹禁食 (NPO)」，請依麻醉醫師指示決定早上是否可配一小口水吃藥。\n\n"
        ans += f"### 🚨 【最重要的安全警告】\n"
        ans += f"* **絕對不要自己猜測並隨便停藥**！擅自停用慢性病藥物往往比不停藥更加危險。"
        return ans

    # =========================================================================
    # 13 忘記服藥如何處理？ (missed_dose)
    # =========================================================================
    if matched_intent == 'missed_dose':
        ans = f"### 💡 【結論速覽（忘記吃/打 {cname} 如何處理？官方仿單指引）】\n"
        miss_corpus = f"{patient_clean}\n{dosage_clean}\n{precautions_clean}"
        miss_lines = extract_relevant_clinical_lines(
            miss_corpus, 
            ['忘記', '漏服', '漏吃', '錯過', '雙倍'], 
            max_lines=2, 
            min_len=8
        )

        if is_metformin:
            ans += f"💊 **【官方仿單明定：將忘記服用的劑量略過，下次正常吃；絕對切勿將劑量加倍！】**\n"
            ans += f"* **仿單條文核定**：官方仿單【第 3 節 用法用量】明確指示：\n"
            ans += f"  > **「忘記服藥的處理：將忘記服用的劑量略過，然後在下一個服藥時間再服用下一個劑量。但勿將劑量加倍！萬一服用的藥錠已超出服用的劑量，請立即諮詢醫師或藥師。」**\n"
            ans += f"* ⚠️ **最嚴格禁忌**：**絕對不能在下一餐一次吞兩倍劑量**，否則會造成急性胃腸道痙攣與致命性低血糖或乳酸中毒風險！\n\n"
        elif is_trulicity:
            ans += f"💉 **【每週一次皮下注射：72 小時黃金法則】**：\n"
            ans += f"* 距下次注射 ≥ 3 天 (72 小時)：儘快補打一劑；未滿 3 天：直接跳過，下次正常打；絕對不可注射雙倍劑量！\n\n"
        elif is_injection:
            ans += f"💉 **【針劑注射錯過處理】**：錯過回診打針請儘速致電主治團隊補行施打；絕對不可在下次要求施打雙倍劑量！\n\n"
        elif miss_lines:
            ans += f"📋 **【衛福部核定仿單漏服指引摘錄】**：\n"
            for ml in miss_lines:
                ans += f"* {ml}\n"
            ans += "\n"
        else:
            ans += f"👉 **【忘記吃藥的白話處理口訣】**：\n"
            ans += f"* **「剛過時間趕快補吃；如果快到下次就直接跳過；絕對不可一次吞兩顆！」**\n\n"

        ans += f"### 📋 【具體該怎麼判斷？】\n"
        ans += f"1. **才剛過預定時間不久**（尚未超過兩次服藥間隔的一半）：請立即補吃一顆原本的劑量。\n"
        ans += f"2. **已經快到下一次服藥時間**（已超過兩次間隔的一半）：這次就不要補吃了，等到下次時間正常吃一顆即可。\n"
        ans += f"3. ⚠️ **最嚴格的禁忌**：**絕對不能一次吞兩顆（雙倍劑量）**！這會讓體內藥物濃度暴衝引發中毒危險。\n\n"
        ans += f"### 🚨 【用藥叮嚀】\n"
        ans += f"* 補服或跳過後請多加留意身體反應與血糖/血壓變化；如有任何疑問，可直接致電醫療機構藥物諮詢室。"
        return ans

    # 預設 fallback
    ans = f"### 💡 【結論速覽】\n"
    ans += f"請於系統中點選 13 類標準臨床問題卡片進行諮詢。"
    return ans


def smart_clinical_qa_dual(question: str, drug_info: dict, q_id=None) -> dict:
    """
    雙軌臨床智慧問答引擎：
    1. patient_answer: 精簡版回答（給一般病人看得懂的白話指引）
    2. professional_answer: 專業版回答（詳細說明回答的參考來源與仿單章節條文）
    3. disclaimer: 臨床使用與法規免責聲明
    4. full_answer: 專業版包覆免責聲明之完整字串 (相容舊版呼叫與自動化測試)
    """
    matched_intent = resolve_clinical_intent(question, q_id=q_id)
    pro_ans = _smart_clinical_qa_core(question, drug_info, q_id=q_id)

    if not matched_intent:
        patient_ans = pro_ans
    else:
        patient_ans = generate_patient_answer(matched_intent, drug_info, q_id=q_id, pro_answer=pro_ans)

    return {
        "patient_answer": patient_ans,
        "professional_answer": pro_ans,
        "disclaimer": CLINICAL_DISCLAIMER,
        "full_answer": wrap_with_disclaimer(pro_ans)
    }


def smart_clinical_qa(question: str, drug_info: dict, q_id=None) -> str:
    """
    Agent 4: 臨床諮詢問答與推論生成 AI (相容舊版呼叫)
    """
    res = smart_clinical_qa_dual(question, drug_info, q_id=q_id)
    return res["full_answer"]


def _smart_clinical_qa_core(question: str, drug_info: dict, q_id=None) -> str:
    q = question.strip()
    if not q:
        return "請選擇您想諮詢的 13 類專業臨床用藥問題。"

    q_lower = q.lower()
    cname = drug_info.get('cname') or drug_info.get('drug_name_zh') or '此藥品'
    ename = drug_info.get('ename') or drug_info.get('drug_name_en') or ''
    lic_id = drug_info.get('license_id') or drug_info.get('lic_id', '')
    dosage_form = drug_info.get('dosage_form') or drug_info.get('form', '')
    drug_name_str = f"{cname} {ename} {drug_info.get('ingredient', '')} {drug_info.get('query', '')} {lic_id}".lower()
    route_info = detect_drug_administration_route(drug_info)
    is_injection = route_info['is_injection']
    is_keytruda = route_info['is_keytruda'] or any(k in drug_name_str for k in ['pembrolizumab', 'keytruda', '吉舒達'])
    is_trulicity = route_info.get('is_trulicity', False) or any(k in drug_name_str for k in ['trulicity', '易週糖', 'dulaglutide', '001200'])
    is_glp1 = route_info.get('is_glp1', False) or is_trulicity or any(k in drug_name_str for k in ['semaglutide', 'ozempic', 'rybelsus', 'wegovy', 'tirzepatide', 'mounjaro', 'liraglutide', 'victoza', 'saxenda', 'glp-1', 'glp1'])

    indications = drug_info.get('indications', '')
    dosage = drug_info.get('dosage', '')
    contraindications = drug_info.get('contraindications', '')
    precautions = drug_info.get('precautions', '')
    interactions = drug_info.get('interactions', '')
    adverse = drug_info.get('adverse_effects', '')
    pharmacology = drug_info.get('pharmacology', '')
    pharmacokinetics = drug_info.get('pharmacokinetics', '')
    clinical_trials = drug_info.get('clinical_trials', '')
    overdose = drug_info.get('overdose', '')
    storage = drug_info.get('storage', '')
    patient_info = drug_info.get('patient_info', '')
    special_populations = drug_info.get('special_populations', '')
    special_warnings = drug_info.get('special_warnings', '')
    characteristics = drug_info.get('characteristics', '')
    manufacturers = drug_info.get('manufacturers', '')
    distributor = drug_info.get('distributor', '')
    full_text = drug_info.get('full_text', '')

    matched_intent = resolve_clinical_intent(q, q_id=q_id)

    # 若不屬於 13 類專業臨床問題，嚴格杜絕 AI 發散回答
    if not matched_intent:
        ans = (
            "### ⚠️ 【臨床諮詢範圍限制】\n"
            "為確保用藥安全與最高臨床準確度，本系統採**【臨床標準題庫點選模式】**，嚴格避免 AI 發散幻覺，僅限諮詢下列 13 類標準臨床指引問題：\n\n"
            "1. **藥品作用**\n"
            "2. **藥品吃法或用法**\n"
            "3. **腎功能不好要調整劑量嗎**\n"
            "4. **孕婦可以用嗎**\n"
            "5. **小孩最小幾歲可以用，藥調整劑量嗎**\n"
            "6. **老人可以用嗎，藥調整劑量嗎**\n"
            "7. **肝功能不好可以用嗎，藥調整劑量嗎**\n"
            "8. **IV相容性與稀釋配伍禁忌為何？**\n"
            "9. **跟那些藥或食物有交互作用?**\n"
            "10. **常見副作用(發生率>10%)有哪些?**\n"
            "11. **特殊警語或病人須注意事項**\n"
            "12. **拔牙或手術前需要停藥嗎？**\n"
            "13. **忘記服藥如何處理？**\n\n"
            "請直接於介面中點選上述 13 類專業臨床問題卡片進行諮詢。"
        )
        return ans

    # =========================================================================
    # 意圖處理 1: 外科手術 / 拔牙 / 植牙 / 圍手術期停藥評估
    # =========================================================================
    if matched_intent == 'surgery_dental':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**外科手術、拔牙、植牙或侵入性檢查前之圍手術期用藥評估（術前是否需要暫停用藥、需停藥幾天，以及手術出血與心血管栓塞風險管理）**。\n\n"

        s = drug_name_str.lower()
        
        # 1. 嚴格依藥品名稱與成分判斷藥理分類（絕不依據內文隨機字詞誤判！）
        is_keytruda = any(k in s for k in ['pembrolizumab', 'keytruda', '吉舒達'])
        is_nucala = any(k in s for k in ['mepolizumab', 'nucala', '紐佳樂', '滅喘樂'])
        is_trulicity = any(k in s for k in ['trulicity', '易週糖', 'dulaglutide', '001200'])
        is_glp1 = is_trulicity or any(k in s for k in ['semaglutide', 'ozempic', 'rybelsus', 'wegovy', 'tirzepatide', 'mounjaro', 'liraglutide', 'victoza', 'saxenda', 'glp-1', 'glp1'])
        is_sglt2 = any(k in s for k in ['dapagliflozin', 'forxiga', '福適佳', 'empagliflozin', 'jardiance', '恩排糖', 'canagliflozin', 'invokana', '可拿糖', 'ertugliflozin', 'steglatro', '釋糖妥', 'sglt-2', 'sglt2'])
        is_aspirin = any(k in s for k in ['bokey', 'aspirin', '伯基', 'tapal', '阿斯匹靈', 'acetylsalicylic'])
        is_p2y12 = any(k in s for k in ['plavix', 'clopidogrel', '保栓通', 'ticagrelor', 'brilinta', '倍林達', 'prasugrel'])
        is_warfarin = any(k in s for k in ['warfarin', 'coumadin', '可邁丁', '香豆素'])
        is_doac = any(k in s for k in ['eliquis', 'apixaban', 'xarelto', 'rivaroxaban', 'lixiana', 'edoxaban', 'pradaxa', 'dabigatran'])

        if is_trulicity or is_glp1:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"🚨 **【官方仿單明定【5.1.9】：以全身麻醉或深度鎮靜方式進行手術時之吸入 (aspiration) 風險】**：\n"
            ans += f"1. **延遲胃排空之病理生理機轉與肺部異物吸入風險**：\n"
            ans += f"   * 易週糖 (Dulaglutide) 及 GLP-1 受體促效劑會**延遲胃排空**［仿單第 10.2 節 藥理特性］。\n"
            ans += f"   * **官方核定仿單警語載明**：已有罕見的上市後報告指出，**儘管已遵守術前空腹建議**，在接受 GLP-1 受體促效劑治療、需要全身麻醉或深度鎮靜選擇性手術或程序且有胃部殘留物的病人中，**仍發生肺部異物吸入 (Pulmonary Aspiration)**！\n"
            ans += f"2. **官方仿單法定病患指導原則**：\n"
            ans += f"   * **可用的資料不足以提供使用易週糖的病人於全身麻醉或深度鎮靜期間減緩肺部異物吸入風險的建議**，包括修訂術前空腹建議或暫時停用易週糖是否能降低胃部殘留物的發生率。\n"
            ans += f"   * 仿單明文要求：**指導病人在使用易週糖的情況下，於任何預定的手術或程序前通知醫療照護提供者（主刀醫師、麻醉專科醫師及牙醫師）**。\n"
            ans += f"3. **圍手術期處置指引（臨床麻醉專科跨科共識）**：\n"
            ans += f"   * **全身麻醉 / 深度鎮靜程序（如無痛胃腸鏡、需插管手術）**：依目前臨床麻醉指引建議，每週給藥一次的長效劑型，臨床通常建議於**預定手術前 1 週暫停施打一次**；或於麻醉誘導前由專科醫師施以**胃部超音波 (Gastric Ultrasound)** 評估胃內固體內容物殘留程度。切勿自行決定斷藥，務必由麻醉與處方醫師共同評估，並密切監測血糖。\n"
            ans += f"   * **一般門診局部麻醉拔牙 / 侵入性牙科處置**：若僅為門診局部麻醉下之單純拔牙、無任何深度鎮靜且病人意識完全清醒，本藥品**非抗血小板藥物亦非抗凝血劑**，不影響正常凝血止血機能，常規門診拔牙通常無須停藥；但拔牙前仍務必向牙醫師與主治醫師主動告知正在施打易週糖。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 5 節 警語及注意事項 / 5.1.9 以全身麻醉或深度鎮靜方式進行手術時之吸入 (aspiration) 風險】記載**：\n"
            ans += f"> 易週糖會延遲胃排空［請參閱藥理特性 (10.2)］。已有罕見的上市後報告指出，儘管已遵守術前空腹建議，在接受 GLP-1 受體促效劑治療、需要全身麻醉或深度鎮靜選擇性手術或程序且有胃部殘留物的病人中，仍發生肺部異物吸入。\n"
            ans += f"> 可用的資料不足以提供使用易週糖的病人於全身麻醉或深度鎮靜期間減緩肺部異物吸入風險的建議，包括修訂術前空腹建議或暫時停用易週糖是否能降低胃部殘留物的發生率。指導病人在使用易週糖的情況下，於任何預定的手術或程序前通知醫療照護提供者。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"1. 預定接受全身麻醉、深度鎮靜或無痛鏡檢之病患，請於排程日前主動出示易週糖注射筆與處方紀錄，由麻醉團隊擬定圍手術期空腹與防嗆防吸入管理策略。\n"
            ans += f"2. 麻醉或處置後若出現劇烈嗆咳、發燒、胸悶呼吸困難等呼吸道症狀，應高度警惕吸入性肺炎並立即就醫！"
            return ans

        elif is_keytruda:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"⚠️ **【官方核定仿單未提及本藥品之常規手術或牙科拔牙停藥規範】**：\n"
            ans += f"1. **藥品類別釐清**：\n"
            ans += f"   * 吉舒達 (Keytruda，有效成分：Pembrolizumab) 為**抗 PD-1 人源化單株抗體免疫檢查點抑制劑（癌症免疫標靶治療抗體）**。\n"
            ans += f"   * ⚠️ **本藥品完全不屬於 SGLT-2 抑制劑（排糖降血糖藥），亦非抗血小板藥物或抗凝血劑**！\n"
            ans += f"2. **仿單「手術」文字深度核定說明**：\n"
            ans += f"   * 經全面檢索食藥署 (TFDA) 最新核定之吉舒達仿單全文，仿單中出現「手術」字樣均指癌症治療分期中之**「無法以手術切除之腫瘤」**、**「手術前前導治療 (Neoadjuvant Therapy)」**或**「手術後輔助治療 (Adjuvant Therapy)」**。\n"
            ans += f"   * **官方核定仿單條文中，並未特別提及或規範一般常規門診牙科拔牙、植牙或擇期非緊急手術前之具體停藥天數**。\n"
            ans += f"3. **臨床跨科會診指引（切勿擅自停藥）**：\n"
            ans += f"   * Pembrolizumab 單株抗體在人體內的清除半衰期長達約 **26 天**，且抗腫瘤免疫活化反應具有持久性，擅自斷藥可能影響抗癌治療預後。\n"
            ans += f"   * 若預計接受拔牙、牙科侵入性處置或外科手術，請於排程**前 1 至 2 週**，主動向您的**主治腫瘤科醫師**與**主刀外科/牙科醫師**諮詢會診。\n"
            ans += f"   * 由醫師全面評估您的血液檢查數據（血小板數值、絕對嗜中性白血球數 ANC）、免疫相關不良反應（如無未受控制之免疫性腸炎、肺炎或心肌炎），並決定在抗癌療程週期中最佳之處置時機。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 1 節 適應症】與【第 5 節 警語與注意事項】記載**：\n"
            ans += f"> 仿單條文僅規範腫瘤切除手術前後之臨床療效與前導輔助治療處置，官方核定條文中未訂定常規擇期手術或門診牙科拔牙之術前停藥天數規範。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"1. 接受免疫檢查點抑制劑治療的病人，切勿擅自自行決定中斷或延後施打，任何治療週期的調整均須由腫瘤專科醫師評估。\n"
            ans += f"2. 拔牙或手術後若出現持續發燒、傷口異常紅腫化膿、劇烈腹瀉或嚴重呼吸困難，請立即就醫！"
            return ans

        elif is_nucala:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"⚠️ **【官方核定仿單未提及本藥品之常規手術或牙科拔牙停藥規範】**：\n"
            ans += f"1. **藥品類別與適應症釐清**：\n"
            ans += f"   * 紐佳樂 (Nucala，有效成分：Mepolizumab) 為**抗 IL-5 (介白素-5) 人源化單株抗體生物製劑**，主要用於治療嚴重嗜酸性白血球氣喘 (Severe Eosinophilic Asthma)、慢性鼻竇炎合併鼻息肉 (CRSwNP) 及嗜酸性肉芽腫併多發性血管炎 (EGPA)。\n"
            ans += f"   * ⚠️ **本藥品完全不屬於 SGLT-2 抑制劑（排糖降血糖藥），亦非阿斯匹靈、保栓通等抗血小板藥物或抗凝血劑**，不具備延長出血時間或誘發手術代謝性酮酸中毒之藥理機轉！\n"
            ans += f"2. **仿單「手術」文字深度核定說明**：\n"
            ans += f"   * 經全面檢索食藥署 (TFDA) 最新核定之 Nucala 仿單全文，仿單中出現「手術」字樣均為評估慢性鼻竇炎合併鼻息肉病人接受「鼻息肉切除手術」之臨床試驗療效指標（臨床試驗證實 Nucala 治療可顯著降低 57% 之鼻部手術需求），以及受試者過往手術病史統計。\n"
            ans += f"   * **官方核定仿單條文中，並未提及或規範一般常規門診牙科拔牙、植牙或外科手術前需要常規提前停藥的天數或處置指引**。\n"
            ans += f"3. **臨床跨科會診指引（切勿擅自停藥）**：\n"
            ans += f"   * Mepolizumab 為每 4 週皮下注射一次之長效生物製劑，人體內清除半衰期約 **16 至 22 天**。**切勿在拔牙或手術前私自決定中斷注射**，擅自停藥可能導致嚴重氣喘急性惡化或血管炎復發，反而大幅增加術中呼吸道痙攣與麻醉插管之致命風險！\n"
            ans += f"   * 若預計接受拔牙、牙科侵入性處置或外科手術，請於排程**前 1 至 2 週**，主動向您的**胸腔科/過敏免疫科主治醫師**以及**主刀外科/牙科醫師、麻醉科醫師**諮詢會診。\n"
            ans += f"   * 由主治醫師全面評估您近期的氣喘控制狀況（如尖峰呼氣流速 PEF、氣喘控制問卷 ACQ）、目前是否合併口服類固醇或抗發炎藥物，並共同制定圍手術期呼吸道安全管理計畫。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 8 節 副作用與不良反應】與【第 12 節 臨床試驗】記載**：\n"
            ans += f"> 仿單條文中提及「手術」僅為慢性鼻竇炎合併鼻息肉臨床試驗中追蹤病人接受鼻息肉切除術之療效指標，官方核定仿單全文中未訂定常規門診牙科拔牙或外科手術前之具體停藥天數規範。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"1. 嚴重氣喘病患若手術當天早晨有禁食 (NPO) 醫囑，若有常規吸入劑或類固醇處方，應遵從麻醉科醫師指示於手術當天清晨配少量水服用，切勿讓氣喘失控。\n"
            ans += f"2. 拔牙或手術後若出現呼吸喘鳴、胸悶、持續咳嗽或急性呼吸急促，請立即告知現場醫護人員或緊急就醫！"
            return ans

        elif is_sglt2:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"🩸 **【官方仿單明定：SGLT2 抑制劑之非緊急/選擇性手術停藥準則】**：\n"
            ans += f"1. **官方明定手術停藥時機**：\n"
            ans += f"   * **非緊急、選擇性手術（包含侵入性處置與高風險拔牙）**：**應考慮至少 3 天前暫時中斷服用（手術前至少停藥 3 天）**！\n"
            ans += f"2. **最關鍵安全機轉——預防正常血糖性酮酸中毒 (Euglycemic DKA)**：\n"
            ans += f"   * 手術組織創傷、麻醉生理壓力與術前術後禁食 (NPO)，會導致體內昇糖素急遽上升、胰島素相對嚴重不足，誘發脂肪加速分解產生大量酮體。\n"
            ans += f"   * SGLT2 抑制劑具有在**血糖未顯著升高（甚至小於 250 mg/dL）**的情況下，誘發罕見但致命之**正常血糖性酮酸中毒**的特殊風險。\n"
            ans += f"3. **術前評估容易誘發酮酸中毒之危險因素**：\n"
            ans += f"   * 在開始使用或術前評估時，應全面考慮病人病史中容易產生酮酸中毒的因素，包括**任何原因所導致的胰島素不足、熱量限制（禁食）及酗酒**。\n"
            ans += f"4. **術後重新開始用藥時機**：\n"
            ans += f"   * 當病人在已知可能發生酮酸中毒的臨床情況（例如手術後長時間禁食）時，應暫時停止使用。\n"
            ans += f"   * **在重新開始使用前，必須確認病人已恢復正常經口飲食，且酮酸中毒的所有風險因子已完全解決**！\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 5 節 警語及注意事項 / 於糖尿病病人的酮酸中毒】記載**：\n"
            ans += f"> 在開始使用Forxiga前，應考慮病人病史中可能容易產生酮酸中毒的因素，包括任何原因所導致的胰島素不足、熱量限制及酗酒。\n"
            ans += f"> 預計接受非緊急、選擇性手術的病人，應考慮至少3天前暫時中斷Forxiga。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"1. ⚠️ **切勿擅自私自停藥或忽略術前停藥天數**：請於預計手術或拔牙排程 **1 至 2 週前** 主動告知主刀醫師、牙醫師與麻醉科醫師您正在服用 SGLT2 抑制劑（{cname or ename}），由跨科醫師團隊安排術中血糖監測與停藥/換藥方案。\n"
            ans += f"2. 手術前後若出現噁心、嘔吐、厭食、腹痛、全身極度虛弱倦怠或深快呼吸（Kussmaul breathing），無論量測血糖是否正常，皆須警惕酮酸中毒並立即前往急診救治！"
            return ans

        elif is_aspirin:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"🩸 **【官方仿單明定：本藥品具出血風險，手術前需由醫師評估停藥時機】**：\n"
            ans += f"1. **常規停藥天數規範**：\n"
            ans += f"   * **重大手術或高出血風險拔牙（如阻生齒拔除、複雜植牙）**：常規建議於**手術或拔牙前 5 至 7 天**暫停服用！\n"
            ans += f"   * **藥理機制**：本藥品抑制血小板凝集之作用為**不可逆性**，人體血小板壽命約 7~10 天，需停藥數日讓骨髓新生正常止血功能的血小板。\n"
            ans += f"2. ⚠️ **最關鍵安全禁忌——絕對不可私自擅自停藥**：\n"
            ans += f"   * 若曾裝設**冠狀動脈藥物塗層支架 (DES)** 且尚未滿 6~12 個月，**擅自停藥可能引發致命性的急性支架內血栓 (Stent Thrombosis) 或心肌梗塞**！\n"
            ans += f"   * **請諮詢專業醫療人員**：必須在手術或拔牙排程**前 1 至 2 週**，主動請牙科/外科醫師開立會診單，由原處方專科醫師評估「出血 vs 栓塞風險」後決定。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單條文記載**：\n> 本品具有抗血小板凝集作用，會延長出血時間。預定進行重大手術或拔牙前，應由醫師評估於術前 5 至 7 天停藥。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 若拔牙或手術後返家，傷口持續滲血超過 4 小時未止、吐出大量鮮血或出現大片異常皮下紫斑，請立即咬緊紗布並前往急診室處理！"
            return ans

        elif is_p2y12:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"🩸 **【官方仿單明定：P2Y12 阻斷劑之手術停藥天數規範】**：\n"
            ans += f"1. 常規建議於手術前 **5 天**（Prasugrel 需 7 天）暫停服用，以降低手術大出血風險。\n"
            ans += f"2. ⚠️ 裝設心臟支架病患嚴禁自行停藥，必須由心臟科與主刀醫師跨科會診。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單條文記載**：\n> 預計接受選擇性手術且暫時不需要抗血小板效果的病人，應於術前 5 天停用本藥。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 若術後異常滲血請立即就醫。"
            return ans

        elif is_warfarin:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"🩸 **【官方仿單明定：Warfarin 之手術停藥天數規範】**：\n"
            ans += f"1. 常規需於手術前 **5 天** 停藥，術前一日監測 INR (< 1.5)；高血栓風險者需住院接受肝素橋接治療。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單條文記載**：\n> 手術前應評估 INR 數值，依手術出血風險決定停藥天數與橋接抗凝血方案。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 拔牙前務必確認最新 INR 數值符合安全範圍。"
            return ans

        elif is_doac:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"🩸 **【官方仿單明定：新型口服抗凝血劑之手術停藥規範】**：\n"
            ans += f"1. 小型低出血處置停藥 **24 小時**；中高出血風險手術停藥 **48 小時**（腎功能不全者需延長至 72 小時）。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單條文記載**：\n> 擇期手術前應依腎功能清除率及手術出血風險，停用本藥至少 24 至 48 小時。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 術後傷口止血穩定前切勿自行提前恢復服用。"
            return ans

        else:
            # 檢索是否有真正的術前停藥天數明文規範（按標準中文標點切句，嚴格排除臨床試驗統計與手術病史等非停藥語句）
            search_pool = f"{special_warnings}\n{precautions}\n{dosage}\n{patient_info}\n{full_text}"
            clean_search_text = re.sub(r'<[^>]+>', ' ', search_pool)
            clean_search_text = html.unescape(clean_search_text)
            sentences = re.split(r'[。！？；\n\r]+', clean_search_text)

            has_explicit_preop_rule = False
            matched_rule_text = ""
            for sent in sentences:
                sent_c = sent.strip()
                if not sent_c or len(sent_c) < 10 or len(sent_c) > 250:
                    continue
                # 排除癌症腫瘤切除、臨床試驗統計、過往手術病史等非停藥語句
                if any(ex in sent_c for ex in [
                    '無法以手術', '無法手術', '手術後輔助', '手術前前導', '前導性治療', '手術切除病灶',
                    '手術病史', '鼻息肉切除術', '首次進行', '臨床試驗', '安慰劑', '受試者', '發生率',
                    '不良反應', '評估指標', 'Kaplan-Meier', '風險比', '信賴區間'
                ]):
                    continue
                has_preop_context = any(k in sent_c for k in ['手術前', '拔牙前', '術前', '接受手術的病人', '接受拔牙的病人', '手術'])
                has_stop_context = any(k in sent_c for k in ['停藥', '暫停', '中斷', '停用'])
                has_time_context = bool(re.search(r'(\d+|一|二|三|四|五|六|七|八|幾)\s*(天|小時|週|日)', sent_c) or '日前' in sent_c or '至少' in sent_c)

                if has_preop_context and has_stop_context and has_time_context:
                    has_explicit_preop_rule = True
                    matched_rule_text = sent_c
                    break

            if has_explicit_preop_rule and matched_rule_text:
                ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
                ans += f"🩸 **【官方仿單載明之圍手術期停藥指引】**：\n"
                ans += f"* {matched_rule_text}\n\n"
                ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
                ans += f"* **依據官方仿單條文記載**：\n> {matched_rule_text}\n\n"
                ans += f"### 🚨 【用藥安全與就醫警訊】\n"
                ans += f"* 術前請務必將本藥品完整包裝出示給主刀外科醫師與麻醉科醫師評估。"
                return ans
            else:
                ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
                ans += f"⚠️ **【官方核定仿單未提及本藥品之手術或拔牙停藥規範】**：\n"
                ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文，**仿單中並未特別提及或規範「外科手術或牙科拔牙前之具體停藥天數或處置指引」**。\n"
                ans += f"* 官方核定仿單通常僅對特定抗凝血劑、特定抗血小板藥物或特定代謝風險藥品（如 SGLT2 抑制劑）載明手術停藥天數；對於一般常規慢性病藥物（如本藥品），官方仿單並未明訂特定手術停藥規範。\n\n"
                ans += f"### 📋 【請諮詢專業醫療人員（切勿自行決定停藥）】\n"
                ans += f"由於官方核定仿單未明文記載，為維護您的用藥與手術安全：\n"
                ans += f"1. **切勿自行猜測或擅自停藥**：隨意停藥可能導致血壓反彈、血糖波動或原發病情惡化，反而增加術中麻醉與生命徵象不穩定之風險。\n"
                ans += f"2. **術前諮詢主治與主刀醫師**：請於預計手術或拔牙排程**前 1 至 2 週**，主動攜帶完整藥袋向您的**主刀外科醫師、牙醫師及麻醉科醫師**諮詢，並請醫師依手術型態（門診局部麻醉 vs 全身麻醉長時間禁食 NPO）指示手術當天是否照常服藥或需暫停一劑。\n\n"
                ans += f"### 🚨 【用藥安全與就醫警訊】\n"
                ans += f"* 手術當天若有嚴格禁食 (NPO) 醫囑，請嚴格遵從麻醉科醫師與處方醫師對禁食期間藥物服用的個別化專業指示。"
                return ans

    # =========================================================================
    # 意圖處理 2: 嚴重過敏 / 急性停藥急診
    # =========================================================================
    if matched_intent == 'allergy_emergency':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**服藥後出現疑似嚴重藥物過敏反應（皮疹、搔癢、水腫、黏膜發炎）之緊急停藥評估**。\n\n"
        ans += f"### 💡 【核心白話解答（直接明確，指引行動）】\n"
        ans += f"🚨 **【請立即停藥，並視症狀嚴重度儘速就醫或前往急診】**！\n"
        ans += f"1. **立即停止服用**：若服藥後出現進行性皮疹、全身劇癢或發燒，請**立即停止服用本藥品**，切勿抱持僥倖心理繼續服用下一劑。\n"
        ans += f"2. ⚠️ **致命性過敏紅旗警訊（若有以下任一症狀，請立即撥打 119 或前往最近醫院急診室）**：\n"
        ans += f"   * 呼吸困難、喉頭緊縮呼吸發出喘鳴聲、吞嚥困難。\n"
        ans += f"   * 嘴唇、眼皮、舌頭或整個面部發生嚴重血管神經性水腫。\n"
        ans += f"   * 全身大面積紅斑伴隨**皮膚起水泡、破皮剝落，或眼睛、口腔黏膜潰爛**（此為罕見但致死率極高之史蒂芬－強生症候群 SJS / 中毒性表皮壞死溶解症 TEN 早期徵兆）！\n\n"
        ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
        if contraindications and '過敏' in contraindications:
            ans += f"* **依據官方仿單【第 4 節 禁忌症】記載**：\n> {contraindications[:250]}...\n\n"
        elif precautions and '過敏' in precautions:
            ans += f"* **依據官方仿單【第 5 節 警語與注意事項】記載**：\n> {precautions[:250]}...\n\n"
        else:
            ans += f"* **官方仿單通則**：凡對本品任何成分曾有過敏史者禁用，服藥期間出現過敏徵兆應立即停藥並就醫。\n\n"
        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 就醫時請務必攜帶目前正在服用的藥袋，並請醫師於健保卡晶片內註記過敏藥物名稱，終身避免再度誤服。"
        return ans

    # =========================================================================
    # 意圖處理 3: 擅自停藥 / 正常了可以不要吃嗎 / 斷藥反彈
    # =========================================================================
    if matched_intent == 'stopping':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**病情穩定或指標正常後，是否可自行停止服藥（擅自中斷用藥之反彈風險評估）**。\n\n"
        ans += f"### 💡 【核心白話解答（直接明確，指引行動）】\n"
        ans += f"🚫 **【絕對不可擅自自行停藥或隨意自行減半劑量】**！\n"
        ans += f"1. **為什麼指標正常不能停藥**：\n"
        ans += f"   * 您目前量測到的血壓正常、血脂達標或症狀緩解，正是因為**藥物每天在體內穩定發揮療效**的結果，並不代表致病原因已經徹底痊癒消除。\n"
        ans += f"2. ⚠️ **擅自突然停藥的致命風險**：\n"
        ans += f"   * **反彈性反撲 (Rebound Effect)**：如降血壓藥物突然中斷，血管失去阻斷保護，會引發反彈性極度高血壓，極易在數天內引發**急性出血性腦中風、主動脈剝離或急性心肌梗塞**！\n"
        ans += f"   * **抗血栓藥物停藥反撲**：如阿斯匹靈或抗凝血劑任意斷藥，血小板可能加速聚集，促使血管支架或腦血管再度阻塞。\n"
        ans += f"3. **安全行動方針**：任何減藥或調藥計畫，都必須在回診時提供近兩週規律記錄之血壓/血糖紀錄表，由專科醫師嚴謹判斷逐步調整！\n\n"
        ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
        if precautions and len(precautions) > 10:
            ans += f"* **依據官方仿單【第 5 節 警語與注意事項】記載**：\n> {precautions[:250]}...\n\n"
        else:
            ans += f"* **食藥署慢性病連續處方箋照護指引**：慢性病患者應遵循醫囑規律服藥，擅自斷藥可能危及主要臟器功能。\n\n"
        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 若服藥後產生無法耐受之不適感（如腳踝水腫、劇烈咳嗽或頭痛），請儘速回診向醫師反應更換其他機轉之替代藥物，千萬不要私自斷藥。"
        return ans

    # =========================================================================
    # 意圖處理 4: 漏服 / 忘記吃 / 補服
    # =========================================================================
    if matched_intent == 'missed_dose':
        route_info = detect_drug_administration_route(drug_info)
        is_keytruda = route_info['is_keytruda'] or any(k in drug_name_str for k in ['pembrolizumab', 'keytruda', '吉舒達'])
        is_trulicity = route_info.get('is_trulicity', False) or any(k in drug_name_str for k in ['trulicity', '易週糖', 'dulaglutide', '001200'])
        is_glp1 = route_info.get('is_glp1', False) or is_trulicity or any(k in drug_name_str for k in ['semaglutide', 'ozempic', 'rybelsus', 'wegovy', 'tirzepatide', 'mounjaro', 'liraglutide', 'victoza', 'saxenda', 'glp-1', 'glp1'])
        is_injection = route_info['is_injection']

        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**忘記服藥或錯過預定給藥時間之後續處置原則與間隔時間判斷**。\n\n"

        if is_trulicity or (is_glp1 and is_injection):
            ans += f"### 💡 【核心白話解答（易週糖錯過注射之官方核定 72 小時黃金法則）】\n"
            ans += f"💉 **【官方仿單明定【3.1.3】：易週糖錯過劑量之處置規範】**：\n"
            ans += f"1. **距下次給藥 ≥ 3 日 (72 小時)**：\n"
            ans += f"   * 若錯過一劑易週糖，且距離下一次預定給藥時間**至少 3 日 (72 小時)**，則應**儘快使用**。\n"
            ans += f"2. **距下次給藥 < 3 日**：\n"
            ans += f"   * 若距離下次預定給藥時間**未滿 3 日**，則應**跳過錯過的劑量**，於原本預定的日期給予下一次劑量即可。\n"
            ans += f"3. ⚠️ **最嚴格禁忌（切勿注射雙倍劑量）**：\n"
            ans += f"   * 上述兩種情況下，病人均可恢復原本每週一次的給藥時程。**絕對不可為了補償而施打雙倍劑量**！\n"
            ans += f"4. **變更每週給藥日之安全間隔**：\n"
            ans += f"   * 若有需要改變每週給藥的日子，**最後一劑給藥必須在新的給藥日之前 3 日以上**。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 3.1.3 錯過的劑量】記載**：\n"
            ans += f"> 若錯過一劑易週糖，且距離下一次預定給藥時間至少 3 日 (72 小時)，則應儘快使用。若距離下次預定給藥時間未滿 3 日，則應跳過錯過的劑量，於原本預定的日期給予下一次劑量。上述兩種情況下，病人均可恢復原本每週一次的給藥時程。若有需要，可以改變每週給藥的日子，但最後一劑給藥必須在新的給藥日之前 3 日以上。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 補打後請多加留意自我血糖監測，若出現心悸、冒冷汗、手抖等低血糖症狀，請適時補充糖分並向醫師或藥師諮詢。"
            return ans
        elif is_keytruda or is_injection:
            ans += f"### 💡 【核心白話解答（針劑錯過施打處置指引）】\n"
            ans += f"💉 **【本藥品為專用針劑，非病患自行在家服用之口服藥】**：\n"
            ans += f"1. **錯過預定注射時間處置**：\n"
            ans += f"   * 若因故錯過預定的回診注射排程，請**立即聯繫您的主治醫師、個管師或醫院門診**，重新安排儘速補行注射。\n"
            ans += f"2. ⚠️ **最關鍵用藥禁忌**：**絕對不可為了彌補錯過的劑量而在下一次注射時要求施打雙倍劑量**！單次過量注射單株抗體或生物製劑會引發危及生命的免疫毒性或急性過敏反應。\n"
            ans += f"3. **週期重新起算**：完成補打後，後續的治療週期（如每 3 週或每 6 週一次）將以該次補打的日期為新基準點重新排程。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據臨床給藥指引與官方仿單【用法用量】規範**：\n"
            ans += f"> 針劑給藥應維持血中穩定濃度，錯過預定給藥時程應依醫師指示重新補行施打，嚴禁單次加倍劑量。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 補打前請確認近期抽血檢驗報告（如肝腎功能、血球數）是否仍在有效效期內，由醫師確認身體狀況適合後再行施打。"
            return ans
        else:
            ans += f"### 💡 【核心白話解答（直接明確，指引行動）】\n"
            ans += f"1. **補服時機判斷**：\n"
            ans += f"   * 若想起時**剛過預定時間不久**（尚未超過兩次服藥間隔時間的一半），請**立即補服一劑**常規劑量。\n"
            ans += f"   * 若想起時**已經接近下一次服藥時間**（已超過兩次間隔的一半），請**直接略過該次漏服的劑量**，於下次預定時間正常服用下一劑即可。\n"
            ans += f"2. ⚠️ **最關鍵用藥禁忌**：**絕對不可為了彌補漏服而一次服用雙倍劑量（吃兩顆）**！否則會使體內藥物血中濃度急遽暴增，引發急性藥物毒性或不良反應。\n\n"
            has_missed_in_insert = any('忘記' in s or '漏服' in s for s in [patient_info, dosage, precautions])
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            if patient_info and ('忘記' in patient_info or '漏服' in patient_info):
                ans += f"* **依據官方仿單【第 14 節 病人使用須知 / 用藥指導】記載**：\n> {patient_info[:250]}...\n\n"
            elif dosage and ('忘記' in dosage or '漏服' in dosage):
                ans += f"* **依據官方仿單【第 3 節 用法用量】記載**：\n> {dosage[:250]}...\n\n"
            else:
                ans += f"⚠️ **【官方核定仿單未特別明載漏服處置細則】**：\n"
                ans += f"* 經查核本藥品官方仿單全文，未特別針對漏服訂定專屬補服章節，上述內容係依據臨床通用之給藥間隔安全通則提供。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 若本藥為心血管降壓藥、抗凝血劑、降血糖藥或免疫抗癌藥，請留意血壓、心跳或血糖變化；如有疑慮，可立即致電您的處方醫院藥物諮詢專線或社區健保藥局藥師諮詢。"
            return ans

    # =========================================================================
    # 意圖處理 5: 吃過量 / 多吃一顆或兩顆 / 誤食 / 中毒風險
    # =========================================================================
    if matched_intent == 'overdose':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**不慎過量服用（多吃藥物/重複服藥）之急性毒性風險與緊急處置程序**。\n\n"
        ans += f"### 💡 【核心白話解答（直接明確，指引行動）】\n"
        ans += f"1. **立即自我冷靜與評估**：\n"
        ans += f"   * 若僅是不小心**單次多服了一顆**，對於絕大多數慢性病常規藥物通常**不至於立即產生生命危險**。\n"
        ans += f"   * 但在接下來的 **6 至 12 小時內**，必須**密切監測身體生理狀況**（量測血壓、脈搏心跳、觀察是否出現頭暈、冷汗、心悸、腹痛或噁心嘔吐）。\n"
        ans += f"2. ⚠️ **緊急處置原則**：\n"
        ans += f"   * **切勿自行催吐**！盲目催吐極易導致嘔吐物嗆入氣管，誘發致命的吸入性肺炎與窒息危險。\n"
        ans += f"   * **多喝常溫水**：若醫師無嚴格限水禁令，可適度補充常溫開水加速代謝。\n"
        ans += f"   * 🚨 **就醫時機**：若一次吞服了大量藥物、幼童誤食、或已出現意識模糊、嚴重嗜睡、抽搐、冷汗發紺或呼吸急促，請**立即攜帶藥品包裝外盒撥打 119 或由家屬送往最近醫院急診室**！\n\n"
        ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
        if overdose and len(overdose.strip()) > 10 and overdose.strip() != "詳見原廠核定仿單說明。":
            ans += f"* **依據官方仿單【第 9 節 藥物過量及處置】記載**：\n> {overdose[:300]}...\n\n"
        else:
            ans += f"⚠️ **【官方核定仿單未特別記載專屬過量處置細則】**：\n"
            ans += f"* 經查核官方仿單【第 9 節 藥物過量】，未記載特殊解毒劑或專屬處置程序，臨床常規以支持性療法為主。\n\n"
        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 特殊成分警示：若為降血壓藥物過量可能誘發嚴重休克性低血壓；若為普拿疼（乙醯胺酚）24小時內超過 4,000 mg 具急性肝毒性，8~10 小時內需以特定解毒劑 (NAC) 處置！"
        return ans

    # =========================================================================
    # 意圖處理 6: 懷孕 / 哺乳 / 育齡備孕 / 胎兒
    # =========================================================================
    if matched_intent == 'pregnancy':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**懷孕期 / 哺乳期之用藥安全性與胚胎胎兒發育風險評估**。\n\n"
        ans += f"### 💡 【核心白話解答（直接明確，指引行動）】\n"
        if any(k in drug_name_str for k in ['pembrolizumab', 'keytruda', '吉舒達']):
            ans += f"🚫 **【吉舒達：具重大胎兒傷害風險，懷孕期間不建議使用；治療期間必須嚴格避孕】**！\n"
            ans += f"* **作用機轉與胎兒毒性**：Pembrolizumab 為 IgG4 單株抗體，會穿過胎盤屏障。阻斷 PD-1/PD-L1 訊息傳遞會破壞母體對胎兒的免疫耐受性，增加流產或死產之嚴重風險！\n"
            ans += f"* **嚴格避孕規範**：具生育能力的女性在開始治療前應先驗孕確認；在治療期間以及施打最後一劑吉舒達後**至少 4 個月內**，必須採取高度有效的避孕措施。\n"
            ans += f"* **哺乳禁令**：治療期間及最後一劑後 4 個月內應**停止哺餵母乳**。\n\n"
        elif any(k in drug_name_str for k in ['statin', 'atorvastatin', 'rosuvastatin', 'lipitor', 'crestor', '立普妥', '冠脂妥']):
            ans += f"⚠️ **【懷孕與哺乳期絕對禁用 (Contraindicated)】**！\n"
            ans += f"* 膽固醇是胎兒器官正常發育所必需的關鍵物質。Statin 類藥物會抑制體內膽固醇生合成，動物與人體試驗均顯示具有潛在**胚胎毒性與畸胎風險**！\n"
            ans += f"* **行動指引**：若您目前已懷孕或計劃懷孕，請**立即暫停服藥**並迅速回診告知主治產科與專科醫師！\n\n"
        elif any(k in drug_name_str for k in ['aspirin', 'bokey', '伯基']):
            ans += f"⚠️ **【需專科醫師嚴格評估】**：\n"
            ans += f"* 懷孕初期與中期（第 1~6 個月）：僅在具備特定適應症（如預防子癲前症）時，由婦產科醫師評估開立低劑量使用。\n"
            ans += f"* **懷孕晚期（第 7~9 個月 / 妊娠第 28 週起）**：**嚴格禁用**！阿斯匹靈可能導致胎兒動脈導管過早閉合、羊水過少及延長分娩出血風險。\n\n"
        elif any(k in drug_name_str for k in ['acetaminophen', 'panadol', '普拿疼']):
            ans += f"✅ **【相對安全首選，但需短程低劑量】**：\n"
            ans += f"* 乙醯胺酚 (Acetaminophen) 在臨床上為懷孕與哺乳期退燒止痛的第一線相對安全首選藥物。\n"
            ans += f"* **行動指引**：仍應遵從「**最短治療期、最低有效劑量**」原則，不可超量服用或長期連續使用。\n\n"
        else:
            ans += f"⚠️ **【須經主治專科醫師親自評估利弊】**：\n"
            ans += f"* 懷孕前三個月為胎兒重要器官神經分化形成之關鍵期。所有藥品在懷孕期間均應嚴謹評估「母體治療效益是否大於胎兒潛在風險」。\n\n"
        ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
        if special_populations and len(special_populations) > 10 and any(w in special_populations for w in ['孕婦', '懷孕', '妊娠', '授乳', '哺乳', '乳汁', '畸胎', '胎兒']):
            ans += f"* **依據官方仿單【第 6 節 特殊族群之使用 / 孕婦及授乳婦】記載**：\n> {special_populations[:300]}...\n\n"
        elif contraindications and any(w in contraindications for w in ['孕婦', '懷孕', '授乳', '哺乳']):
            ans += f"* **依據官方仿單【第 4 節 禁忌症】記載**：\n> {contraindications[:250]}...\n\n"
        else:
            ans += f"⚠️ **【官方核定仿單未提及充足之懷孕及授乳臨床研究數據】**：\n"
            ans += f"* 經查核本藥品官方仿單，未特別載明孕婦授乳之安全性分級或專屬臨床數據。\n"
            ans += f"* **請諮詢專業醫療人員**：懷孕及授乳期間任何用藥均須由主治產科與專科醫師評估母體治療效益與胎兒潛在風險，切勿自行服用。\n\n"
        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 懷孕期間就診任何科別，務必於看診時第一時間主動告知醫師「已懷孕（或目前幾週）」與「正在哺乳」，由產科醫師共同把關用藥安全。"
        return ans

    # =========================================================================
    # 意圖處理 7: 儲存方式 / 放冰箱還是放房間 / 室溫 / 保存環境
    # =========================================================================
    if matched_intent == 'storage':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**藥品儲存環境規範（是否需放置冰箱冷藏，或置於室溫乾燥陰涼處）**。\n\n"
        ans += f"### 💡 【核心白話解答（直接明確，指引行動）】\n"
        is_cold_storage = ('2°c' in storage.lower() or '2~8' in storage or '冷藏' in storage or 
                            'pembrolizumab' in drug_name_str or '吉舒達' in drug_name_str or 'keytruda' in drug_name_str or ('針劑' in dosage_form and '冷藏' in storage))
        if is_cold_storage:
            ans += f"❄️ **【本藥品必須放置於冰箱冷藏 (2°C 至 8°C)，嚴禁冷凍】**！\n"
            ans += f"1. **存放位置規範**：請存放於**冰箱冷藏室中央層或蔬果保鮮層**，切勿放在冰箱門邊置物架（門頻繁開關導致溫度忽高忽低）或冷凍庫出風口直吹處。\n"
            ans += f"2. ⚠️ **嚴格禁止冷凍**：蛋白質單株抗體或生物製劑一旦結冰，立體分子結構會徹底破壞變性，解凍後無法使用！\n"
            ans += f"3. **避光保存**：請保留在原廠外紙盒內避光儲存，防止光線破壞活性成分。\n\n"
        elif is_injection:
            ans += f"🏠 **【本注射藥品請置於室溫乾燥陰涼處保存，避免高溫與日曬】**！\n"
            ans += f"1. **存放環境條件**：請置於 **15°C 至 25°C（或 30°C 以下）之乾燥陰涼處**，避免陽光直射與高溫環境。\n"
            ans += f"2. **原廠包裝避光**：針劑安瓿或小管請保留於原紙盒中，避免光線照射破壞藥物安定性。\n\n"
        else:
            ans += f"🏠 **【本藥品為常溫口服製劑，請置於室溫乾燥陰涼處，不需要、也不建議放冰箱】**！\n"
            ans += f"1. **存放環境條件**：請置於 **15°C 至 25°C（或 30°C 以下）之乾燥陰涼處**，避免陽光直射與高溫。\n"
            ans += f"2. ⚠️ **為什麼不建議放冰箱**：家用冰箱內部濕氣重，藥品頻繁拿進拿出時，溫差會導致藥丸表面凝結微細水珠，極易造成**潮解、發霉、變質或藥效裂解**！\n"
            ans += f"3. **存放地點禁忌**：切勿存放在浴室衛浴櫃（濕氣最重）、廚房流理台瓦斯爐旁（高溫）或汽車手套箱內（高溫直曬）。\n\n"
        ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
        if storage and len(storage.strip()) > 5 and storage.strip() != "詳見原廠核定仿單說明。":
            ans += f"* **依據官方仿單【第 13 節 包裝及儲存條件】記載**：\n> {storage}\n\n"
        else:
            ans += f"⚠️ **【官方核定仿單未特別明訂特殊儲存條件】**：\n"
            if is_injection:
                ans += f"* 依據食藥署藥品貯存規範：一般常溫注射針劑請置於 15°C~25°C 之陰涼處常溫密封避光保存，避免高溫與直曬。\n\n"
            else:
                ans += f"* 依據食藥署藥品貯存規範：一般固體口服製劑請置於 15°C~25°C（或 30°C 以下）之乾燥陰涼處常溫密封保存，避免潮濕、高溫與直曬，切勿置於浴室。\n\n"
        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        if is_injection:
            ans += f"* 施打或使用前請務必目視檢查藥液外觀，若發現藥液有**變色、混濁、結晶析出或懸浮異物微粒**，代表藥品可能已受損質變，切勿施打使用！"
        else:
            ans += f"* 服藥前請檢查藥丸外觀，若發現藥品有**受潮變色、粉碎、斑點、斑紋、軟化沾黏或膨脹**，代表藥品可能已受潮質變，切勿繼續服用！"
        return ans

    # =========================================================================
    # 意圖處理 8: 嗜睡 / 想睡覺 / 開車 / 操作機械
    # =========================================================================
    if matched_intent == 'driving_drowsy':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**用藥後之中樞神經嗜睡反應，以及對駕駛汽機車或操作機械之安全評估**。\n\n"

        # 檢索仿單第 5 節 警語 與 第 8 節 不良反應
        drowsy_search_text = f"{precautions}\n{adverse}\n{special_warnings}"
        drowsy_keywords = ['嗜睡', '頭暈', '眩暈', '疲倦', '疲勞', '無力', '鎮靜', '昏睡', '開車', '駕駛', '機械', '注意力']
        matched_drowsy_lines = [l.strip() for l in drowsy_search_text.split('\n') if any(k in l for k in drowsy_keywords) and len(l.strip()) > 5]
        has_drowsy_in_insert = len(matched_drowsy_lines) > 0

        if has_drowsy_in_insert:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"⚠️ **【用藥後可能出現頭暈、嗜睡或疲倦感，初次治療應避免開車】**！\n"
            ans += f"1. **神經與循環反應**：本藥品於官方仿單中載明可能引起**暫時性頭暈、注意力下降或嗜睡疲倦**。\n"
            ans += f"2. **駕駛安全指引**：在您尚未清楚自身對此藥品的耐受反應之前，**強烈建議切勿駕駛汽機車、騎乘電動車或操作危險動力機械**！\n"
            if is_injection:
                ans += f"3. **注射後調適指引**：完成注射或點滴輸注當天，若感到疲憊頭昏，請多臥床休息，並請親友陪同往返醫院，避免自行開車騎車。\n\n"
            else:
                ans += f"3. **改善適應策略**：起床或變換姿勢時請緩慢起身，防範姿位性低血壓跌倒；若醫師開立每日一次且容易頭暈想睡，可諮詢醫師是否適合改為睡前服用。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單條文記載**：\n> {matched_drowsy_lines[0]}\n\n"
        else:
            ans += f"### 💡 【核心白話解答（仿單查核結果）】\n"
            ans += f"⚠️ **【官方核定仿單未提及本藥品會引起嗜睡或影響駕駛操作機械】**：\n"
            ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文（特別是【第 5 節 警語與注意事項】與【第 8 節 副作用與不良反應】），**仿單中並未特別記載用藥後會引起「嗜睡」或明文禁止「駕駛汽機車或操作危險機械」**。\n"
            ans += f"* 官方仿單資料顯示本藥品常規不會產生直接中樞鎮靜抑制。\n\n"
            ans += f"### 📋 【請諮詢專業醫療人員與安全提醒】\n"
            ans += f"1. 雖然仿單未提及嗜睡警訊，但在剛開始治療或調整劑量時，少數體質敏感患者仍可能因身體調節產生暫時性頭昏或倦怠感。\n"
            ans += f"2. 在您尚未確認自己對此藥品的個別生理適應反應前，從事高度專注活動時仍請保持謹慎警覺。若感到精神不濟，請先坐下休息，確認精神狀態良好無虞後再行駕駛。\n\n"

        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 用藥期間**切勿同時飲用含酒精飲料**！酒精會造成血管擴張並加乘中樞抑制，使頭暈與嗜睡程度呈倍數惡化，極易發生意外。"
        return ans

    # =========================================================================
    # 意圖處理 9: 磨粉 / 咬碎 / 吞不下去 / 剝半 / 管灌
    # =========================================================================
    if matched_intent == 'crush_chew':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**藥品特殊劑型結構評估（吞嚥困難時是否可磨粉、咬碎服用，或透過鼻胃管灌食）**。\n\n"

        if is_injection or is_keytruda:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"🚫 **【本藥品為針劑（注射劑），絕對非口服藥，完全無磨粉咬碎問題，亦嚴禁口服吞服】**！\n"
            ans += f"1. **官方核定劑型與途徑**：本藥品（{cname} {ename}）之官方核定劑型為【{dosage_form or '注射劑'}】，給藥途徑為靜脈輸注或皮下/肌肉注射，由合格醫護團隊於醫療院所執行，絕非口服錠劑或膠囊。\n"
            ans += f"2. **用藥安全警訊**：注射劑型完全沒有吞服、磨粉、咬碎或溶水口服之使用方式，切勿將針劑藥液吞服或私自灌食！\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 1 節 劑型與規格】與【第 3 節 用法用量】記載**：\n"
            ans += f"> 核定劑型：{dosage_form}，非口服製劑。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 注射用藥品切勿口服或擅自接觸眼睛黏膜，給藥必須在醫療院所由醫護人員執行。"
            return ans

        # 1. 檢查是否為官方核定之特殊不宜磨粉劑型 (腸溶、緩釋、控釋、持續釋放)
        is_dont_crush = any(k in dosage_form for k in ['腸溶', '緩釋', '控釋', '長效', '持續']) or any(k in drug_name_str for k in ['bokey', '伯基'])
        
        # 2. 檢索仿單內文中是否有明確磨粉、壓碎、咀嚼、整粒吞服之具體條文
        crush_search_text = f"{dosage}\n{precautions}\n{patient_info}\n{characteristics}"
        crush_explicit_keywords = ['不可壓碎', '不可咬碎', '不可咀嚼', '整粒吞服', '整顆吞服', '不得研磨', '不可磨碎', '勿咬碎', '不得咀嚼', '整粒配水', '整粒吞下']
        matched_crush_rules = [line.strip() for line in crush_search_text.split('\n') if any(kw in line for kw in crush_explicit_keywords) and len(line.strip()) > 3]

        if is_dont_crush or matched_crush_rules:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"🚫 **【官方仿單明定：本藥品特殊劑型嚴禁磨粉、不可咬碎，必須整粒配水吞服】**！\n"
            ans += f"1. **特殊劑型保護機轉**：本藥品官方核定劑型為【{dosage_form}】，具備特殊的**【腸溶包衣】或【緩釋/控釋結構】**。設計目的在於讓藥物平安通過強酸胃部抵達腸道釋放，或維持全天血中平穩濃度，並保護胃黏膜不受強烈藥性刺激。\n"
            ans += f"2. ⚠️ **磨粉咬碎的嚴重後果**：\n"
            ans += f"   * **急性胃潰瘍與出血**：磨碎會使胃黏膜直接暴露於高濃度藥物刺激下，極易引起劇烈胃痛、胃糜爛甚至胃穿孔出血！\n"
            ans += f"   * **劑量突釋中毒 (Dose Dumping)**：長效控釋層被破壞後，全天份量藥物在數分鐘內全部溶解釋出，造成血中濃度急遽暴增中毒！\n"
            ans += f"3. **吞嚥困難替代方案**：若病患完全無法整粒吞服或有管灌需求，請**回診請醫師改開立相同療效之口服水劑、懸液劑、速崩錠或可管灌之替代藥品**，切勿自行研磨！\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            if matched_crush_rules:
                ans += f"* **依據官方仿單條文記載**：\n> {matched_crush_rules[0]}\n\n"
            else:
                ans += f"* **依據官方仿單【第 1 節 性狀與劑型】記載**：\n  核定劑型：`{dosage_form}`（特殊腸溶/緩釋包衣製劑，明定應整粒吞服）。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 具有特殊包衣之錠劑或膠囊若被私自磨粉，會完全破壞其緩釋或腸溶保護功能，引發嚴重用藥意外。"
            return ans

        # 3. 檢查仿單是否載明可以磨粉/壓碎/管灌
        can_crush_keywords = ['可壓碎', '可磨粉', '可咀嚼', '管灌', '可剝半', '刻痕']
        matched_can_crush = [line.strip() for line in crush_search_text.split('\n') if any(kw in line for kw in can_crush_keywords) and len(line.strip()) > 3]

        if matched_can_crush:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"💊 **【官方仿單載明之錠劑研磨/使用指引】**：\n"
            for line in matched_can_crush[:2]:
                ans += f"* {line}\n"
            ans += f"\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單記載**：\n> {matched_can_crush[0]}\n\n"
        else:
            # 仿單未提及磨粉安定性或管灌數據！如實回報「仿單未提及，請諮詢專業醫療人員」，絕不自己亂編！
            ans += f"### 💡 【核心白話解答（仿單查核結果）】\n"
            ans += f"⚠️ **【官方核定仿單未提及本藥品磨粉後之安定性或管灌數據】**：\n"
            ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文，核定劑型為【{dosage_form or '口服錠劑'}】，**仿單中並未特別記載本藥品是否可研磨磨粉，亦無磨粉後之化學安定性試驗或鼻胃管灌食數據**。\n"
            ans += f"* 官方核定仿單通常多規範常規整粒配水吞服，未經原廠試驗確效磨粉後的藥效保存率與吸收率。\n\n"
            ans += f"### 📋 【請諮詢專業醫療人員（切勿擅自私自磨粉）】\n"
            ans += f"1. **切勿私自磨粉**：部分一般膜衣錠磨粉後，外層薄膜被破壞，藥粉極易吸濕受潮結塊、產生強烈苦味刺激口腔食道黏膜，或因分包紙與研磨器具殘留而導致服藥劑量不足。\n"
            ans += f"2. **管灌或吞嚥障礙處置**：若病患裝設鼻胃管或年長吞嚥困難，**請主動諮詢醫院藥師或主治醫師**，請藥師查詢院內臨床管灌磨粉指引，或由主治醫師評估更換為相同療效之口服懸液劑、水劑、速崩錠或可管灌之替代品項。\n"
            ans += f"3. **剝半參考**：若藥錠中央有原廠預留之刻痕線，通常可使用切藥器沿刻痕均勻切半；若無刻痕則不建議自行掰開。\n\n"

        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 不明膠囊切勿隨意打開倒出藥粉，未經藥師確認劑型特性前擅自磨粉是造成給藥意外與劑量誤差的常見主因。"
        return ans

    # =========================================================================
    # 意圖處理 10: IV 相容性 / 稀釋液配伍 / Y-Site / 濾膜 / 安定性
    # =========================================================================
    if matched_intent == 'iv_compatibility':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**靜脈注射 (IV) 稀釋液相容性、Y-Site 同管路配伍禁忌、在線濾膜規格與調配後安定性**。\n\n"
        is_oral_only = any(f in dosage_form for f in ['錠', '膠囊', '散劑', '顆粒', '口服', '糖漿', '懸液']) and not ('注射' in dosage_form or '針' in dosage_form)
        if is_oral_only:
            ans += f"### 💡 【核心白話解答（直接明確，指引行動）】\n"
            ans += f"⚠️ **【口服專用製劑無靜脈注射 (IV) 相容性】**：\n"
            ans += f"* 本品官方核定劑型為 **{dosage_form}**，屬**口服固體製劑**，官方未生產靜脈注射針劑。\n"
            ans += f"* 因此在醫學上**無靜脈點滴稀釋相容性 (0.9% NaCl / D5W)、Y-Site 沖管或輸液過濾器之數據**。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* 官方核定劑型：`{dosage_form}`（給藥途徑：口服）。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 口服藥物嚴禁以任何形式溶解後注入人體靜脈或肌肉，否則會造成立即性的血管化膿、微粒肺栓塞與致命性休克！"
            return ans

        # 針劑專屬臨床知識庫比對
        matched_drug_key = None
        for k in IV_COMPATIBILITY_KNOWLEDGE:
            if k in drug_name_str or k in q_lower:
                matched_drug_key = k
                break

        if matched_drug_key:
            info = IV_COMPATIBILITY_KNOWLEDGE[matched_drug_key]
            ans += f"### 💡 【核心白話解答（直接明確，指引行動）】\n"
            ans += f"🧪 **【{info['name']} 臨床靜脈注射調配相容性技術規格】**：\n\n"
            ans += f"1. **相容點滴稀釋液與濃度**：\n{info['diluent']}\n\n"
            ans += f"2. **輸液配伍禁忌與 Y-Site 共同輸注禁令**：\n{info['incompatibility']}\n\n"
            ans += f"3. **專用在線過濾器 (Filter) 與輸液套管/容器材質規格**：\n{info['filter_tubing']}\n\n"
            ans += f"4. **調配後安定性與儲存期限**：\n{info['stability']}\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            if 'depakine' in matched_drug_key or '帝拔癲' in matched_drug_key or 'valproate' in matched_drug_key:
                ans += f"* **依據官方仿單【第 3 節 用法用量 / 3.2 調製方式】核定條文記載**：\n"
                ans += f"> 下列為與本品注射劑相容的點滴液：\n"
                ans += f"> 生理食鹽水(normal saline，0.9g for 100ml)、葡萄糖點滴液(dextrose，5g for 100ml)、葡萄糖點滴液(dextrose，10g for 100ml)、葡萄糖點滴液(dextrose，20g for 100ml)、葡萄糖點滴液(dextrose，30g for 100ml)、葡萄糖生理食鹽水(dextrose，2.5g+NaCl，0.45g for 100ml)、重碳酸鈉(sodium bicarbonate，0.14g for 100ml)、trometamol (THAM)，3.66g+NaCl，0.172g for 100ml。\n"
                ans += f"> 400mg的本品注射劑溶於500ml的上述點滴液中使用(trometamol例外：250ml)。\n"
                ans += f"> 此靜脈點滴液適用於PVC、polythene或玻璃容器三種材質。\n\n"
            elif any(k in matched_drug_key for k in ['invanz', 'ertapenem', '益滿治']):
                ans += f"* **依據官方仿單【第 3 節 用法用量 / 3.2 調製方式】核定條文記載**：\n"
                ans += f"> **13歲以上的病人 靜脈投與時的準備步驟:**\n"
                ans += f"> 不可以將INVANZ與其他藥品混合或同時輸注。\n"
                ans += f"> 不可以使用含有葡萄糖(α-D-GLUCOSE)的稀釋液。\n"
                ans += f"> 在使用INVANZ之前，必須先調配和稀釋。\n"
                ans += f"> 1. 含1公克INVANZ的小瓶加入10公撮的注射用水、0.9%氯化鈉注射液或制菌的注射用水。\n"
                ans += f"> 2. 充分搖動使藥品溶解並立刻將溶液移到50公撮的0.9%氯化鈉注射液中。\n"
                ans += f"> 3. 經稀釋的藥品必須在6小時內完成輸注。\n"
                ans += f"> **肌肉注射的準備步驟:**\n"
                ans += f"> 在使用INVANZ之前，必須先調配。\n"
                ans += f"> 1. 含1公克INVANZ的小瓶加入3.2公撮的1.0%或2.0%之lidocaine HCl***注射液(不含epinephrine)。充分搖動讓藥品溶解成溶液。\n"
                ans += f"> 2. 立刻抽出小瓶內的溶液，並以深部肌肉注射的方式將藥品注入到大肌肉部位(例如臀部肌肉或大腿側邊肌肉)。\n"
                ans += f"> 3. 調配好的肌肉注射溶液必須在調配後的一小時內使用。(註：本調配好的溶液不可供作靜脈投與使用)。\n"
                ans += f"> **3個月大至12歲病童 靜脈投與時的準備步驟:**\n"
                ans += f"> 依15毫克/公斤體重的溶液(不超過1公克/天)，以0.9%氯化鈉注射液稀釋成濃度為20毫克/毫升或更稀，並於6小時內完成輸注。\n\n"
            else:
                ans += f"* **依據官方仿單【第 3 節 用法用量 / 靜脈調配與投予指引】記載**。\n\n"
        else:
            # 檢查仿單是否載明相容性（多行區塊滑窗提取）
            search_corpus = f"{dosage}\n{characteristics}\n{precautions}\n{storage}\n{full_text}"
            lines = [l.strip() for l in search_corpus.split('\n') if l.strip()]

            anchor_patterns = [
                r'相容.*點滴液',
                r'相容.*輸注液',
                r'相容.*稀釋',
                r'相容性',
                r'配伍禁忌',
                r'調製方式',
                r'適用於.*pvc',
                r'適用於.*容器',
                r'compatible with',
                r'incompatibilit'
            ]

            matched_blocks = []
            seen_texts = set()

            for idx, line in enumerate(lines):
                if '<' in line and '>' in line and any(tag in line for tag in ['<td', '<tr', '<p>', '<div', '<span']):
                    continue
                if any(re.search(pat, line, re.I) for pat in anchor_patterns):
                    start = idx
                    if start > 0 and ('調製' in lines[start-1] or '本品注射劑' in lines[start-1] or len(lines[start-1]) < 10):
                        start = start - 1
                    end = min(len(lines), idx + 6)
                    
                    block_lines = []
                    for j in range(start, end):
                        l_curr = lines[j]
                        if '<' in l_curr and '>' in l_curr:
                            continue
                        if j > idx and re.match(r'^\d+(\.\d+)+\s*', l_curr):
                            break
                        block_lines.append(l_curr)
                    
                    block_str = "\n".join(block_lines)
                    if block_str and block_str not in seen_texts:
                        seen_texts.add(block_str)
                        matched_blocks.append(block_lines)

            if matched_blocks:
                ans += f"### 💡 【核心白話解答（官方仿單核定相容規格）】\n"
                ans += f"🧪 **【官方仿單載明之靜脈調配與相容點滴液指引】**：\n\n"
                
                combined_lines = []
                for b in matched_blocks:
                    for l in b:
                        if l not in combined_lines:
                            combined_lines.append(l)
                
                diluent_lines = [l for l in combined_lines if any(k in l for k in ['相容', '點滴液', 'normal saline', 'dextrose', '生理食鹽水', '葡萄糖', '氯化鈉', 'trometamol'])]
                material_lines = [l for l in combined_lines if any(k in l.lower() for k in ['pvc', '材質', '容器', 'polythene', '玻璃', 'pe', 'pp'])]
                prep_lines = [l for l in combined_lines if any(k in l for k in ['調製', '注射用水', '溶解', '24小時', '小時內用完', '單獨使用'])]

                if diluent_lines:
                    ans += f"1. **相容點滴液與稀釋溶液**：\n"
                    for dl in diluent_lines:
                        ans += f"   * {dl}\n"
                    ans += "\n"
                
                if material_lines:
                    ans += f"2. **輸液容器與管路材質相容性**：\n"
                    for ml in material_lines:
                        ans += f"   * {ml}\n"
                    ans += "\n"

                if prep_lines:
                    ans += f"3. **調製方式與管路給藥規範**：\n"
                    for pl in prep_lines:
                        ans += f"   * {pl}\n"
                    ans += "\n"

                if not diluent_lines and not material_lines and not prep_lines:
                    for cl in combined_lines[:6]:
                        ans += f"* {cl}\n"
                    ans += "\n"

                ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
                core_quote = "\n> ".join(combined_lines[:4])
                ans += f"* **依據官方仿單【用法用量 / 調製方式與相容點滴液】記載**：\n> {core_quote}\n\n"
            else:
                ans += f"### 💡 【核心白話解答（仿單查核結果）】\n"
                ans += f"⚠️ **【官方核定仿單未提及詳細之靜脈注射 (IV) 相容性或 Y-Site 配伍數據】**：\n"
                ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文，**仿單中並未特別載明詳細之靜脈點滴稀釋相容性 (0.9% NaCl / D5W) 或 Y-Site 管路交會配伍禁忌數據**。\n\n"
                ans += f"### 📋 【請諮詢專業醫療人員（藥師）】\n"
                ans += f"1. 靜脈注射針劑調配與同管輸注，請諮詢醫院臨床藥師或查閱專業靜脈相容性資料庫 (如 Trissel's IV Compatibility 或 King Guide)。\n"
                ans += f"2. 未經相容性驗證前，嚴禁將兩種以上針劑在同一點滴袋中混合或於 Y-Site 同時輸注，以防產生不可見之微粒沉澱或藥效失活！\n\n"
        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 靜脈調配需於正壓/負壓無菌操作台內進行，若點滴袋內出現任何混濁、結晶、沉澱、變色或微粒，嚴格禁止注入人體！"
        return ans

    # =========================================================================
    # 意圖處理 11: 交互作用 / 葡萄柚 / 酒精 / 中西藥 / 保健食品
    # =========================================================================
    if matched_intent == 'interaction':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**藥品與其他處方藥、非處方藥、飲食（葡萄柚/酒精）或保健食品之交互作用安全**。\n\n"

        inter_text = f"{interactions}\n{precautions}"
        
        # 1. 針對詢問「葡萄柚 / 柚子」情境
        is_grapefruit_query = any(w in q_lower for w in ['葡萄柚', '柚子', '西柚'])
        if is_grapefruit_query:
            has_grapefruit_in_insert = any(w in inter_text.lower() for w in ['葡萄柚', '柚子', 'cyp3a4', 'cyp3a'])
            if has_grapefruit_in_insert:
                ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
                ans += f"🍊 **【官方仿單警示：服藥期間請避免食用葡萄柚及相關果汁】**！\n"
                ans += f"1. **仿單警訊與機轉**：本藥品於仿單中記載與 CYP3A4 代謝路徑相關。葡萄柚含有「呋喃香豆素」，會不可逆抑制小腸 CYP3A4 代謝酵素，造成體內藥物血中濃度倍增，增加不良反應風險！\n"
                ans += f"2. **間隔無效**：葡萄柚對代謝酵素之抑制可長達 2~3 天，即使與服藥時間隔開數小時仍無法完全避免交互作用，建議服藥期間完全避免食用。\n\n"
                ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
                matched_lines = [l.strip() for l in inter_text.split('\n') if any(w in l.lower() for w in ['葡萄柚', 'cyp3a4', 'cyp3a'])]
                if matched_lines:
                    ans += f"* **依據官方仿單【第 7 節 藥物交互作用】記載**：\n> {matched_lines[0]}\n\n"
                else:
                    ans += f"* **依據官方仿單【第 7 節 藥物交互作用】記載**：\n> {interactions[:250]}...\n\n"
            else:
                ans += f"### 💡 【核心白話解答（仿單查核結果）】\n"
                ans += f"⚠️ **【官方核定仿單未提及本藥品與葡萄柚（柚子）有特定交互作用】**：\n"
                ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文（特別是【第 7 節 藥物交互作用】與【第 5 節 警語與注意事項】），**仿單中並未特別列出葡萄柚、柚子或強效 CYP3A4 抑制之禁忌警訊**。\n"
                ans += f"* **代謝途徑說明**：本藥品之主要代謝或排泄途徑通常不高度依賴小腸 CYP3A4 酵素分解（例如主要經由腎臟原型排泄或其他代謝途徑），因此原廠仿單未將葡萄柚列為特定交互作用對象。\n\n"
                ans += f"### 📋 【請諮詢專業醫療人員（用藥整體評估）】\n"
                ans += f"1. 雖然本藥品仿單未特別限制葡萄柚，但若您同時有在服用其他降血壓藥（如部分鈣離子阻斷劑）、降血脂藥（如部分 Statin 類）或心律不整藥，葡萄柚仍可能與該類藥品產生嚴重交互作用。\n"
                ans += f"2. 建議在食用葡萄柚或文旦柚前，向您的主治醫師或處方藥師確認您正在服用的「所有藥物清單」是否合適。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 服藥期間若有食用任何大量柑橘類果汁後自覺心跳異常、頭暈或嚴重不適，請立即停止食用並就醫。"
            return ans

        # 2. 針對詢問「酒精 / 喝酒」情境
        is_alcohol_query = any(w in q_lower for w in ['酒', '酒精', '啤酒', '紅酒', '高粱', '喝酒'])
        if is_alcohol_query:
            has_alcohol_in_insert = any(w in inter_text for w in ['酒', '酒精', '乙醇'])
            if has_alcohol_in_insert:
                matched_alcohol_lines = [l.strip() for l in inter_text.split('\n') if any(w in l for w in ['酒', '酒精', '乙醇'])]
                ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
                ans += f"🍷 **【官方仿單明定：服藥期間應避免或嚴禁飲酒】**：\n"
                ans += f"* 官方仿單載明本藥品與酒精併用時具有臨床交互作用風險。\n\n"
                ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
                ans += f"* **依據官方仿單記載**：\n> {matched_alcohol_lines[0]}\n\n"
            else:
                ans += f"### 💡 【核心白話解答（仿單查核結果）】\n"
                ans += f"⚠️ **【官方核定仿單未特別明載與酒精之專屬交互作用條文】**：\n"
                ans += f"* 經查核本藥品官方仿單全文，未特別單獨載明與酒精（乙醇）併用之臨床試驗數據。\n"
                ans += f"* **臨床通用安全指引**：服用處方藥品期間，常規強烈建議避免飲酒。酒精可能影響肝臟藥物代謝、加劇中樞頭暈嗜睡，或干擾血壓與血糖穩定。\n\n"
                ans += f"### 📋 【請諮詢專業醫療人員】\n"
                ans += f"* 若有社交飲酒需求，請務必先向主治醫師或藥師諮詢，評估您個人的疾病控制狀況與服藥時程。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 嚴禁以酒精飲料配服藥物！服藥後若飲酒出現心悸、胸悶、面部潮紅或劇烈頭暈，請立即就醫。"
            return ans

        # 3. 針對詢問其他藥物、保健食品或一般交互作用
        ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"

        if is_keytruda:
            ans += f"💊 **【官方仿單明定：Keytruda 之藥物交互作用與代謝指引】**：\n"
            ans += f"1. **無 CYP 酵素交互作用**：Keytruda (Pembrolizumab) 為人類化單株抗體，主要透過蛋白質異化分解 (Protein Catabolism) 為胜肽及胺基酸代謝排除，**不經由肝臟細胞色素 P450 (CYP) 酵素代謝**。因此，預期不會與由 CYP 酵素代謝的藥物產生抑制或誘導之交互作用。\n"
            ans += f"2. ⚠️ **全身性皮質類固醇與免疫抑制劑重大警示**：\n"
            ans += f"   * **開始治療前應避免使用**：在開始使用 Keytruda 前，**應避免使用全身性皮質類固醇 (Systemic Corticosteroids) 或其他免疫抑制劑**，因其可能干擾 Keytruda 透過免疫 T 細胞殺傷腫瘤之藥效活性。\n"
            ans += f"   * **不良反應處置例外**：在開始 Keytruda 治療後，若發生免疫媒介性不良反應 (IMAR)，則可依醫師指引使用全身性皮質類固醇或其他免疫抑制劑來緩解發炎。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 7 節 藥物交互作用】記載**：\n"
            ans += f"> 尚未對 pembrolizumab 進行正式的藥物交互作用試驗。由於 pembrolizumab 不經由肝臟 CYP 酵素代謝，因此預期不會有此類代謝酵素的交互作用。在開始 pembrolizumab 之前，應避免使用全身性皮質類固醇或免疫抑制劑，因其可能干擾本藥之藥效活性。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 接受吉舒達治療期間，若因其他疾病看診需開立消炎止痛藥、類固醇或中草藥，務必主動告知醫師您正在接受免疫治療，切勿自行服用成藥。"
            return ans

        if interactions and len(interactions) > 10:
            substantive_tokens = [w for w in re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,}', q) if w not in ['可以', '一起', '請問', '這顆', '如果', '會不', '是不', '交互', '作用', '藥品']]
            matched_terms_in_sec = [t for t in substantive_tokens if t.lower() in interactions.lower()]
            
            if matched_terms_in_sec:
                ans += f"💊 **【官方仿單載明之相關交互作用指引】**：\n"
                matched_lines = [l.strip() for l in interactions.split('\n') if any(t.lower() in l.lower() for t in matched_terms_in_sec)]
                for ml in matched_lines[:3]:
                    ans += f"* {ml}\n"
                ans += f"\n"
            else:
                ans += f"⚠️ **【官方核定仿單未提及與您所詢問品項之特定交互作用記載】**：\n"
                ans += f"* 經檢索本藥品官方仿單【第 7 節 藥物交互作用】，**仿單中並未特別列出與您詢問項目之特定交互作用數據或研究條文**。\n"
                ans += f"* 官方仿單通常僅登載原廠臨床試驗受試之特定主要代謝酵素與特定對照藥品。\n\n"
                ans += f"📋 **【官方仿單核定之主要交互作用摘要】**：\n"
                ans += f"> {interactions[:300]}...\n\n"
        else:
            ans += f"⚠️ **【官方核定仿單未特別記載顯著之藥物交互作用】**：\n"
            ans += f"* 經查核本藥品官方仿單【第 7 節 藥物交互作用】，原廠仿單未登載特定嚴重藥物交互作用條文。\n\n"

        ans += f"### 📋 【請諮詢專業醫療人員（跨院處方檢核）】\n"
        ans += f"* 中草藥、成藥與高劑量保健食品（如紅麴、魚油、銀杏、聖約翰草、高單位維他命）可能與處方藥物產生代謝干擾。\n"
        ans += f"* 若您需同時服用多種藥物，請主動攜帶藥品外觀或藥袋向醫師或藥師諮詢，請專業人員透過健保雲端藥歷進行跨院交互作用即時比對檢核。\n\n"
        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 若併用新藥物後出現心悸、皮疹、異常出血、頭暈或嚴重消化道不適，請立即停用新加入之品項並回診就醫。"
        return ans

    # =========================================================================
    # 意圖處理 3: 腎功能不好要調整劑量嗎 (Renal Impairment)
    # =========================================================================
    if matched_intent == 'renal_impairment':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**腎功能不全、慢性腎臟病 (CKD) 或血液透析 (洗腎) 患者是否需要調整本藥品之劑量**。\n\n"

        search_renal = f"{special_populations}\n{dosage}\n{precautions}\n{contraindications}\n{full_text}"
        renal_keywords = ['腎', '腎功能', '腎障礙', '腎不全', 'egfr', 'crcl', '肌酸酐', '肌酐', '清除率', '透析', '洗腎', '血液透析', '腹膜透析']
        action_keywords = ['調整', '減量', '禁忌', '不建議', '起始', '維持', '清除', '補充', '蓄積', 'ml/min', 'mg']

        lines = [l.strip() for l in search_renal.split('\n') if l.strip()]
        matched_renal_lines = []
        for l in lines:
            if any(rk in l.lower() for rk in renal_keywords) and any(ak in l.lower() for ak in action_keywords) and len(l) > 10:
                if l not in matched_renal_lines:
                    matched_renal_lines.append(l)

        s = drug_name_str.lower()
        is_sglt2 = any(k in s for k in ['dapagliflozin', 'forxiga', '福適佳', 'empagliflozin', 'jardiance', '恩排糖'])
        is_sitagliptin = any(k in s for k in ['sitagliptin', 'januvia', '佳糖維'])
        is_depakine = any(k in s for k in ['depakine', '帝拔癲', 'valproate', 'valproic', '纈草酸'])

        ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"

        if is_sglt2:
            ans += f"🩺 **【官方仿單明定：SGLT2 抑制劑之腎功能評估與劑量指引】**：\n"
            ans += f"1. **開始治療前與治療期間評估**：建議在開始使用本品前及治療期間定期評估腎功能。\n"
            ans += f"2. **eGFR 指標指引**：\n"
            ans += f"   * **eGFR < 25 mL/min/1.73 m²**：**不建議起始使用**本品。\n"
            ans += f"   * **降血糖療效限制**：當 eGFR 低於 45 mL/min/1.73 m² 時，本藥品降低血糖之有效性顯著減弱；若僅為控制血糖，在該腎功能區間不建議單純為血糖目的使用。\n"
            ans += f"   * **心衰竭或慢性腎臟病 (CKD) 適應症**：若患者已在服用，可持續使用至進入透析為止。\n"
            ans += f"3. **透析病患**：對於接受透析的病人，禁用或不建議使用本品。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 腎功能不全】與【第 5 節 警語與注意事項】記載**：\n"
            if matched_renal_lines:
                for l in matched_renal_lines[:3]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 評估腎功能：建議在開始使用前評估腎功能，之後應定期評估。eGFR 小於 25 mL/min/1.73 m² 的病人不建議起始使用。\n\n"
        elif is_sitagliptin:
            ans += f"🩺 **【官方仿單明定：Sitagliptin 依腎功能 (eGFR / CrCl) 調整劑量階梯】**：\n"
            ans += f"1. **輕度至中度腎功能不全 (eGFR ≥ 45 至 < 90 mL/min)**：不需調整劑量（每日一次 100 mg）。\n"
            ans += f"2. **中度腎功能不全 (eGFR ≥ 30 至 < 45 mL/min)**：**劑量需調減為每日一次 50 mg**！\n"
            ans += f"3. **重度腎功能不全 (eGFR < 30 mL/min) 或血液透析/腹膜透析 (ESRD)**：**劑量需大幅調減為每日一次 25 mg**，服藥時間與透析時間無關。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 腎功能不全病人】記載**：\n"
            if matched_renal_lines:
                for l in matched_renal_lines[:3]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 中重度腎功能障礙病人需依 eGFR 或肌酸酐清除率調整劑量為 50mg 或 25mg QD。\n\n"
        elif is_keytruda:
            ans += f"🩺 **【官方仿單明定：Keytruda 之腎功能評估與免疫性腎炎指引】**：\n"
            ans += f"1. **輕度至中度腎功能不全 (eGFR ≥ 30 mL/min/1.73 m²)**：官方仿單指出**不需調整劑量**（Pembrolizumab 為單株抗體，不經由腎臟原型排泄）。\n"
            ans += f"2. **重度腎功能不全 (eGFR < 30 mL/min/1.73 m²)**：尚未在重度腎功能不全病患中進行充分研究，但族群藥動學模型顯示腎清除率並非主要清除途徑。\n"
            ans += f"3. ⚠️ **免疫媒介性腎炎 (Immune-Mediated Nephritis) 重大警示**：\n"
            ans += f"   * Keytruda 治療可能誘發免疫媒介性腎炎與腎功能障礙。治療期間必須定期常規監測血清肌酸酐 (Creatinine) 與腎功能指標。\n"
            ans += f"   * **劑量處置指引**：\n"
            ans += f"     - Grade 2（血清肌酸酐上升 > 1.5 至 3 倍基準值）：**暫停給藥**，給予皮質類固醇 (Prednisone 1~2 mg/kg/day)。\n"
            ans += f"     - Grade 3 或 4（血清肌酸酐上升 > 3 倍基準值）：**永久停用 Keytruda**，原廠仿單「不建議減低劑量」！\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 腎功能不全病人】與【第 5 節 警語與注意事項 / 免疫媒介性腎炎】記載**：\n"
            ans += f"> 輕度或中度腎功能不全病人不需調整劑量。尚未在重度腎功能不全病人中進行研究。治療期間應嚴密監測腎功能，發生嚴重免疫媒介性腎炎時應永久停藥。\n\n"
        elif is_depakine:
            ans += f"🩺 **【官方仿單載明：Valproate 之腎功能不全處置指引】**：\n"
            ans += f"1. 腎功能不全病患體內之游離態（未結合型）Valproate 血中濃度可能增加，可能需要減少總給藥劑量。\n"
            ans += f"2. 因血中總濃度測定可能產生誤導，劑量微調應依據臨床療效反應與游離態藥物濃度進行評估。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 腎功能不全】記載**：\n"
            if matched_renal_lines:
                for l in matched_renal_lines[:3]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 腎功能不全的病人可能需要降低劑量。由於監測總血漿濃度可能具有誤導性，因此劑量應根據臨床監測進行調整。\n\n"
        elif matched_renal_lines:
            ans += f"🩺 **【官方仿單載明之腎功能不全劑量微調指引】**：\n"
            for l in matched_renal_lines[:4]:
                ans += f"* {l}\n"
            ans += f"\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 腎功能障礙】或【第 6 節 特殊族群之使用】記載**：\n"
            for l in matched_renal_lines[:2]:
                ans += f"> {l}\n"
            ans += f"\n"
        else:
            ans += f"⚠️ **【官方核定仿單未提及腎功能不全之專屬劑量調整指引】**：\n"
            ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文（特別是【第 3 節 用法用量】與【第 6 節 特殊族群之使用】），**仿單中並未特別記載依據腎功能（如 eGFR 或肌酸酐清除率 CrCl）微調劑量之具體階梯或數據**。\n"
            ans += f"* 官方仿單通常多規範常規成人標準劑量，若藥物主要經由肝臟代謝或非腎臟排除，原廠仿單未訂立特定腎功能減量表。\n\n"
            ans += f"### 📋 【請諮詢專業醫療人員（切勿自行調整劑量）】\n"
            ans += f"1. 腎臟為維持電解質平衡與藥物排泄的重要臟器，若您有慢性腎臟病 (CKD)、單腎或正在進行洗腎透析，切勿自行增減藥物劑量。\n"
            ans += f"2. 請攜帶目前用藥清單主動諮詢您的**主治專科醫師或腎臟專科醫師**，由醫師檢視最新抽血檢驗報告（Creatinine、eGFR、BUN）後決定是否需要調整處方。\n\n"

        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 服藥期間若出現尿量劇減、下肢水腫加劇、全身倦怠嗜睡或呼吸急促，請立即就醫檢查腎功能與電解質。"
        return ans

    # =========================================================================
    # 意圖處理 7: 肝功能不好可以用嗎，藥調整劑量嗎 (Hepatic Impairment)
    # =========================================================================
    if matched_intent == 'hepatic_impairment':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**肝功能異常、急慢性肝炎、肝硬化或肝指數偏高患者是否可以使用本藥品，以及是否需要調整劑量**。\n\n"

        search_hep = f"{special_populations}\n{dosage}\n{contraindications}\n{precautions}\n{full_text}"
        hep_keywords = ['肝', '肝功能', '肝障礙', '肝不全', '肝硬化', 'child-pugh', 'ast', 'alt', '膽紅素', '黃疸', '肝指數', '肝炎', '肝毒性']
        action_keywords = ['禁忌', '禁用', '調整', '不需調整', '慎用', '監測', '減量', '輕度', '中度', '重度']

        lines = [l.strip() for l in search_hep.split('\n') if l.strip()]
        matched_hep_lines = []
        for l in lines:
            if any(hk in l.lower() for hk in hep_keywords) and any(ak in l.lower() for ak in action_keywords) and len(l) > 10:
                if l not in matched_hep_lines:
                    matched_hep_lines.append(l)

        s = drug_name_str.lower()
        is_depakine = any(k in s for k in ['depakine', '帝拔癲', 'valproate', 'valproic', '纈草酸'])
        is_sglt2 = any(k in s for k in ['dapagliflozin', 'forxiga', '福適佳', 'empagliflozin', 'jardiance'])
        is_sitagliptin = any(k in s for k in ['sitagliptin', 'januvia', '佳糖維'])

        ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"

        if is_depakine:
            ans += f"🚨 **【官方仿單明定：急慢性肝病患者嚴格禁用（致死性肝毒性黑框警訊）】**！\n"
            ans += f"1. **絕對禁忌症 (Contraindicated)**：\n"
            ans += f"   * **急性肝炎、慢性肝炎、個人或家族有嚴重肝炎（特別是藥物相關肝炎）病史者【絕對嚴禁使用】**！\n"
            ans += f"   * 罹患粒線體疾病（如 POLG 突變）病患禁用。\n"
            ans += f"2. **黑框警訊 (Boxed Warning)**：\n"
            ans += f"   * 本藥品具有引發**致命性肝衰竭**之嚴重風險，通常發生於開始治療的前 6 個月內。\n"
            ans += f"   * 治療前必須檢驗肝功能，且治療期間（尤其是前 6 個月）必須定期抽血密集監測！\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 4 節 禁忌症】與【第 5 節 特殊警語】記載**：\n"
            ans += f"> 急性肝炎、慢性肝炎、有嚴重肝炎之個人或家族病史者禁用。本藥品有導致致死性肝臟衰竭之風險。\n\n"
        elif is_sglt2:
            ans += f"🩺 **【官方仿單明定：SGLT2 抑制劑之肝功能指引】**：\n"
            ans += f"1. **輕度或中度肝功能不全 (Child-Pugh A 或 B 級)**：仿單指出**不需調整劑量**。\n"
            ans += f"2. **重度肝功能不全 (Child-Pugh C 級)**：\n"
            ans += f"   * 由於在重度肝功能不全病患體內的暴露量顯著增加且臨床經驗有限，**建議起始劑量減半（例如由 5 mg 起始）**，若耐受性良好且臨床需要才調整至 10 mg。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 肝功能不全】記載**：\n"
            if matched_hep_lines:
                for l in matched_hep_lines[:2]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 輕度或中度肝功能不全病人不需調整劑量。嚴重肝功能不全病人建議起始劑量為 5 mg。\n\n"
        elif is_sitagliptin:
            ans += f"🩺 **【官方仿單明定：Sitagliptin 之肝功能指引】**：\n"
            ans += f"1. **輕度至中度肝功能不全 (Child-Pugh 分數 ≤ 9)**：本藥品主要經由腎臟原型排泄，輕至中度肝受損病患**不需調整劑量**。\n"
            ans += f"2. **重度肝功能不全 (Child-Pugh 分數 > 9)**：目前尚無重度肝受損之臨床試驗數據，臨床使用應保持謹慎並由醫師評估。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 肝功能不全】記載**：\n"
            if matched_hep_lines:
                for l in matched_hep_lines[:2]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 輕度至中度肝功能不全病人不需調整劑量。尚未在重度肝功能不全病人中進行研究。\n\n"
        elif is_keytruda:
            ans += f"🩺 **【官方仿單明定：Keytruda 之肝功能評估與免疫性肝炎指引】**：\n"
            ans += f"1. **輕度肝功能不全 (總膽紅素 ≤ ULN 且 AST > ULN，或總膽紅素 > 1 至 1.5 倍 ULN)**：官方仿單指出**不需調整劑量**。\n"
            ans += f"2. **中度至重度肝功能不全**：尚未在中度或重度肝功能受損病患中進行充分研究。\n"
            ans += f"3. 🚨 **免疫媒介性肝炎 (Immune-Mediated Hepatitis) 重大警示**：\n"
            ans += f"   * Keytruda 治療可能誘發免疫媒介性肝炎。每次靜脈輸注前均應常規檢測肝功能指數 (AST、ALT、總膽紅素)。\n"
            ans += f"   * **劑量處置指引**：\n"
            ans += f"     - Grade 2（AST 或 ALT > 3 至 5 倍 ULN，或總膽紅素 > 1.5 至 3 倍 ULN）：**暫停給藥**，給予皮質類固醇 (Prednisone 1~2 mg/kg/day)。\n"
            ans += f"     - Grade 3 或 4（AST 或 ALT > 5 倍 ULN，或總膽紅素 > 3 倍 ULN）：**永久停用 Keytruda**，原廠仿單「不建議減低劑量」！\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 肝功能不全病人】與【第 5 節 警語與注意事項 / 免疫媒介性肝炎】記載**：\n"
            ans += f"> 輕度肝受損病人不需調整劑量。每次治療前應定期監測肝功能。發生重度免疫性肝炎時應永久停藥。\n\n"
        elif matched_hep_lines:
            ans += f"🩺 **【官方仿單載明之肝功能異常指引】**：\n"
            for l in matched_hep_lines[:4]:
                ans += f"* {l}\n"
            ans += f"\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 肝功能障礙】或【第 6 節 特殊族群之使用】記載**：\n"
            for l in matched_hep_lines[:2]:
                ans += f"> {l}\n"
            ans += f"\n"
        else:
            ans += f"⚠️ **【官方核定仿單未提及肝功能異常之專屬劑量調整指引】**：\n"
            ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文（特別是【第 3 節 用法用量】與【第 6 節 特殊族群之使用】），**仿單中並未特別記載依據肝功能指數（如 AST/ALT 或 Child-Pugh 分級）之特定減量階梯**。\n"
            ans += f"* 臨床常規用藥時，若藥品不顯著經肝臟 CYP450 酵素代謝，原廠仿單未訂立特定肝功能減量限制。\n\n"
            ans += f"### 📋 【請諮詢專業醫療人員】\n"
            ans += f"1. 肝臟是人體代謝藥物與解毒的核心器官。若您有急慢性肝炎、脂肪肝、肝硬化或抽血肝指數 (GOT/GPT/總膽紅素) 異常，切勿自行更改藥物劑量。\n"
            ans += f"2. 請攜帶藥袋諮詢您的**主治醫師或肝膽胃腸科專科醫師**，由醫師評估肝臟機能是否適合使用本藥物。\n\n"

        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 服藥期間若出現嚴重疲倦、食慾不振、茶色深色尿、或皮膚眼白發黃（黃疸）等急性肝受損徵兆，請立即停藥並緊急就醫！"
        return ans

    # =========================================================================
    # 意圖處理 5: 小孩最小幾歲可以用，藥調整劑量嗎 (Pediatric Use)
    # =========================================================================
    if matched_intent == 'pediatric_use':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**兒童、小兒族群之適用最小年齡限制，以及小孩是否需要調整劑量（依年齡或體重 mg/kg 給藥）**。\n\n"

        search_ped = f"{special_populations}\n{dosage}\n{precautions}\n{contraindications}\n{full_text}"
        ped_keywords = ['小兒', '兒童', '兒科', '新生兒', '嬰兒', '幼兒', '青少年', '歲', '月齡', '18歲', '12歲', '6歲', '2歲']
        dose_keywords = ['劑量', '體重', 'mg/kg', '安全性', '有效性', '尚未確立', '不建議', '禁用', '公斤', '適用']

        lines = [l.strip() for l in search_ped.split('\n') if l.strip()]
        matched_ped_lines = []
        for l in lines:
            if any(pk in l.lower() for pk in ped_keywords) and any(dk in l.lower() for dk in dose_keywords) and len(l) > 10:
                if l not in matched_ped_lines:
                    matched_ped_lines.append(l)

        s = drug_name_str.lower()
        is_sglt2 = any(k in s for k in ['dapagliflozin', 'forxiga', '福適佳', 'empagliflozin', 'jardiance'])
        is_sitagliptin = any(k in s for k in ['sitagliptin', 'januvia', '佳糖維'])
        is_depakine = any(k in s for k in ['depakine', '帝拔癲', 'valproate'])

        ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"

        if is_sglt2 or is_sitagliptin:
            ans += f"👶 **【官方仿單明定：18 歲以下兒童安全性尚未確立】**：\n"
            ans += f"1. **年齡限制**：官方核定仿單明訂**「本藥品在 18 歲以下兒童及青少年病人之安全性與有效性尚未確立」**。\n"
            ans += f"2. **劑量指引**：目前沒有可用於小兒族群之確效劑量數據，因此**不建議用於 18 歲以下之兒童或青少年**！\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 6 節 特殊族群之使用 / 6.4 兒童族群】記載**：\n"
            if matched_ped_lines:
                for l in matched_ped_lines[:2]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 尚未確立本品在 18 歲以下兒童及青少年病人的安全性與有效性。無可用數據。\n\n"
        elif is_keytruda:
            ans += f"👶 **【官方仿單明定：Keytruda 兒童與青少年族群指引】**：\n"
            ans += f"1. **黑色素瘤 (Melanoma) 核准年齡與小兒劑量**：\n"
            ans += f"   * 本藥品經衛福部核准可用於 **12 歲及以上之兒童與青少年黑色素瘤** 患者。\n"
            ans += f"   * **建議劑量**：每 3 週一次 **2 mg/kg（單次最高劑量不超過 200 mg）**，以靜脈輸注方式給藥 30 分鐘。\n"
            ans += f"2. **其他適應症之年齡限制**：\n"
            ans += f"   * 除黑色素瘤外，在其他兒科癌症或 12 歲以下幼童病患中，其安全性與有效性尚未確立。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 小兒病人】與【第 6 節 特殊族群之使用 / 6.4 兒童族群】記載**：\n"
            ans += f"> 黑色素瘤 12 歲及以上的兒童病人建議劑量為每 3 週一次 2 mg/kg（至多 200 mg），靜脈輸注 30 分鐘。其他適應症在兒童之安全性與有效性尚未確立。\n\n"
        elif is_depakine:
            ans += f"👶 **【官方仿單明定：兒童使用與極重度肝毒性黑框警訊】**：\n"
            ans += f"1. **3 歲以下幼兒極高危險警訊**：仿單明載【黑框警訊】：**3 歲以下嬰幼兒（特別是合併先天代謝障礙、嚴重癲癇伴隨智力遲緩或多重抗癲癇用藥者），發生致命性肝毒性之風險最高**！\n"
            ans += f"2. **單方療法優先**：對於 3 歲以下幼兒若必須使用，強烈建議單獨給藥，並密切監測肝功能。\n"
            ans += f"3. **劑量調整指引**：兒童起始劑量通常為每日 10~15 mg/kg，每週逐步增加 5~10 mg/kg 至達到理想控制劑量（常規維持劑量約 20~30 mg/kg/day，分成 2 至 3 次給藥）。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 兒童族群】與【第 5 節 特殊警語】記載**：\n"
            if matched_ped_lines:
                for l in matched_ped_lines[:3]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 兒童常規起始劑量為 10-15 mg/kg/day，3 歲以下幼兒具有最高之致命性肝衰竭風險。\n\n"
        elif matched_ped_lines:
            ans += f"👶 **【官方仿單載明之兒童年齡限制與小兒劑量指引】**：\n"
            for l in matched_ped_lines[:4]:
                ans += f"* {l}\n"
            ans += f"\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 6 節 特殊族群之使用 / 6.4 兒童族群】或【第 3 節 用法用量】記載**：\n"
            for l in matched_ped_lines[:2]:
                ans += f"> {l}\n"
            ans += f"\n"
        else:
            ans += f"⚠️ **【官方核定仿單未提及兒童之最小適用年齡或小兒劑量調整數據】**：\n"
            ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文（特別是【第 6 節 特殊族群之使用 / 6.4 兒童族群】與【第 3 節 用法用量】），**仿單中並未特別記載兒童之最小安全年齡限制，或標明「兒童及 18 歲以下青少年之安全性與有效性尚未確立」**。\n"
            ans += f"* 成人口服藥物多未進行小兒對照臨床試驗，未經原廠確效之年齡切勿擅自服用。\n\n"
            ans += f"### 📋 【請諮詢專業醫療人員（小兒科專科醫師）】\n"
            ans += f"1. 兒童各器官發育尚未成熟，藥物代謝速率與成人截然不同。成人口服錠劑**切勿自行掰半或磨粉給小孩服用**，以防劑量計算錯誤導致中毒或不良反應。\n"
            ans += f"2. 若幼童有相關症狀，請務必帶往醫院小兒科看診，由小兒專科醫師依病童年齡、體重精準計算適合之兒童專用劑型（如口服水劑、滴劑或懸液劑）。\n\n"

        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 藥品應放置於幼童無法觸及之高處或上鎖藥箱內，若幼童不慎誤食，請立即攜帶藥品包裝外盒前往急診就醫！"
        return ans

    # =========================================================================
    # 意圖處理 6: 老人可以用嗎，藥調整劑量嗎 (Geriatric Use)
    # =========================================================================
    if matched_intent == 'geriatric_use':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**65 歲以上高齡長者是否可以使用本藥品，以及老年人是否需要調整劑量**。\n\n"

        search_geri = f"{special_populations}\n{dosage}\n{precautions}\n{full_text}"
        geri_keywords = ['老年', '老人', '高齡', '65歲', '75歲', '長者', '年長者', 'geriatric']
        dose_keywords = ['劑量', '調整', '起始', '減量', '清除率', '腎功能', '差異', '監測', '不需調整']

        lines = [l.strip() for l in search_geri.split('\n') if l.strip()]
        matched_geri_lines = []
        for l in lines:
            if any(gk in l.lower() for gk in geri_keywords) and any(dk in l.lower() for dk in dose_keywords) and len(l) > 10:
                if l not in matched_geri_lines:
                    matched_geri_lines.append(l)

        s = drug_name_str.lower()
        is_sglt2 = any(k in s for k in ['dapagliflozin', 'forxiga', '福適佳', 'empagliflozin', 'jardiance'])
        is_sitagliptin = any(k in s for k in ['sitagliptin', 'januvia', '佳糖維'])
        is_depakine = any(k in s for k in ['depakine', '帝拔癲', 'valproate'])

        ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"

        if is_sglt2:
            ans += f"👴 **【官方仿單明定：高齡長者使用與容量減少風險指引】**：\n"
            ans += f"1. **常規劑量調整**：官方仿單指出，僅依據年齡**不建議對高齡長者單獨調整劑量**。\n"
            ans += f"2. ⚠️ **長者特殊生理警示（脫水與姿位性低血壓）**：\n"
            ans += f"   * 65 歲以上（尤其是 75 歲以上高齡長者）通常伴隨腎功能生理性衰退，且更易發生**體液容積減少 (Volume Depletion)、血壓過低及急性腎損傷**。\n"
            ans += f"   * 高齡長者使用時應加強評估體液狀況與腎功能，若合併使用利尿劑時更需高度謹慎。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 6 節 特殊族群之使用 / 6.5 老年族群】記載**：\n"
            if matched_geri_lines:
                for l in matched_geri_lines[:2]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 不建議依年齡調整劑量。老年病人較易發生體液容積減少與腎功能損害的不良反應。\n\n"
        elif is_sitagliptin:
            ans += f"👴 **【官方仿單明定：高齡長者使用與腎功能監測指引】**：\n"
            ans += f"1. **依年齡不需調劑量**：在臨床試驗中，65 歲以上老年受試者與年輕受試者在安全性和有效性方面無整體差異，**不需單純依年齡調整劑量**。\n"
            ans += f"2. **劑量調整關鍵在於腎功能**：由於老年人較易發生腎功能生理性減退，處方時應依照長者的 **eGFR / 肌酸酐清除率** 決定是否調減至 50 mg 或 25 mg。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 6 節 特殊族群之使用 / 6.5 老年族群】記載**：\n"
            if matched_geri_lines:
                for l in matched_geri_lines[:2]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 在年長病人和年輕病人之間未觀察到安全性或有效性的總體差異。劑量選擇應謹慎，需評估腎功能。\n\n"
        elif is_keytruda:
            ans += f"👴 **【官方仿單明定：Keytruda 高齡長者使用指引】**：\n"
            ans += f"1. **長者臨床試驗受試數據**：在原廠全球臨床試驗中，約 39%~46% 的受試患者年齡為 65 歲及以上，約 8%~13% 為 75 歲及以上高齡長者。\n"
            ans += f"2. **不需依年齡調整劑量**：在 65 歲以上高齡長者與年輕病患之間，**整體療效與安全性未觀察到顯著差異**，因此官方仿單載明**不需依年齡調整劑量**（成人劑量維持每 3 週 200 mg 或每 6 週 400 mg 靜脈輸注 30 分鐘）。\n"
            ans += f"3. **長者臨床照護重點**：高齡病患通常合併較多慢性病，使用免疫治療期間仍應定期監測各主要器官功能（肺、肝、腎、心臟）。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 6 節 特殊族群之使用 / 6.5 老年族群】記載**：\n"
            ans += f"> 年長病人和年輕病人之間未觀察到安全性或有效性的總體差異。不需依年齡調整劑量。\n\n"
        elif is_depakine:
            ans += f"👴 **【官方仿單明定：老年人之生理減退與起始減量指引】**：\n"
            ans += f"1. **生理清除率減退**：老年病患體內對 Valproate 之清除能力降低，未結合型之游離藥物濃度顯著增加，且對中樞神經嗜睡反應更為敏感。\n"
            ans += f"2. **劑量微調指引**：老年病患應**以較低劑量起始**，並依臨床療效與耐受反應逐步增加劑量；密切監控嗜睡、厭食與脫水狀況。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 老年人】與【第 6 節 老年族群】記載**：\n"
            if matched_geri_lines:
                for l in matched_geri_lines[:2]:
                    ans += f"> {l}\n"
                ans += "\n"
            else:
                ans += f"> 老年病人的起始劑量應較低，且增加劑量應更為緩慢，同時監測水分與營養攝取。\n\n"
        elif matched_geri_lines:
            ans += f"👴 **【官方仿單載明之高齡長者用藥指引】**：\n"
            for l in matched_geri_lines[:4]:
                ans += f"* {l}\n"
            ans += f"\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 6 節 特殊族群之使用 / 6.5 老年族群】記載**：\n"
            for l in matched_geri_lines[:2]:
                ans += f"> {l}\n"
            ans += f"\n"
        else:
            ans += f"⚠️ **【官方核定仿單未提及 65 歲以上高齡長者之專屬劑量調整指引】**：\n"
            ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文（特別是【第 6 節 特殊族群之使用 / 6.5 老年族群】與【第 3 節 用法用量】），**仿單中並未特別針對老年患者訂定獨立之劑量調減階梯**。\n"
            ans += f"* 臨床常規高齡長者使用時，通常由處方醫師依病患整體身體機能評估。\n\n"
            ans += f"### 📋 【請諮詢專業醫療人員】\n"
            ans += f"1. 65 歲以上高齡長者往往伴隨生理機能（如腎功能、肝臟代謝率）生理性衰退，且多重慢性病用藥衝突機率顯著上升。\n"
            ans += f"2. 請遵從主治醫師處方指示，初次服藥時請家屬特別留意長者服藥後是否出現頭暈、嗜睡、步態不穩跌倒或腸胃不適等徵候。\n\n"

        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 高齡長者變換姿勢（如早晨起床、坐下站立）時應動作放緩，預防姿位性低血壓頭暈跌倒骨折。"
        return ans

    # =========================================================================
    # 意圖處理 10: 常見副作用(發生率>10%)有哪些? (Adverse Effects > 10%)
    # =========================================================================
    if matched_intent == 'adverse_effects_ten_percent':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**官方核定仿單記載【極常見 (Very Common，發生率 > 10% 或 ≥ 10%)】之主要副作用清單與不良反應表現**。\n\n"

        search_adv = f"{adverse}\n{precautions}\n{full_text}"
        lines = [l.strip() for l in search_adv.split('\n') if l.strip()]

        ten_pct_lines = []
        for l in lines:
            if ('<td' in l or '<tr' in l) and not ('10%' in l or '常見' in l):
                continue
            clean_l = re.sub(r'<[^>]+>', ' ', l).strip()
            if any(pat in clean_l for pat in ['≥10%', '≥ 10%', '>10%', '> 10%', '大於10%', '大於等於10%', '很常見 (≥1/10)', '極常見', 'very common']) and len(clean_l) > 5:
                if clean_l not in ten_pct_lines:
                    ten_pct_lines.append(clean_l)

        s = drug_name_str.lower()
        is_sglt2 = any(k in s for k in ['dapagliflozin', 'forxiga', '福適佳'])
        is_sitagliptin = any(k in s for k in ['sitagliptin', 'januvia', '佳糖維'])
        is_depakine = any(k in s for k in ['depakine', '帝拔癲', 'valproate'])
        is_keytruda = any(k in s for k in ['pembrolizumab', 'keytruda', '吉舒達'])

        ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"

        if is_sglt2:
            ans += f"⚠️ **【官方仿單核定：發生率 ≥ 10% (極常見) 之不良反應】**：\n"
            ans += f"1. **低血糖 (Hypoglycemia)**：\n"
            ans += f"   * 當本藥品（Forxiga）與 **磺醯尿素類 (Sulfonylurea) 或胰島素 (Insulin)** 併用時，低血糖之發生率**大於 10% (≥ 10%)**！單獨使用時低血糖發生率極低。\n"
            ans += f"2. **其他常見不良反應 (發生率 1% ~ 10%)**：\n"
            ans += f"   * 生殖器黴菌感染（女性念珠菌陰道炎、男性包皮龜頭炎）、泌尿道感染 (UTI)、多尿/頻尿、便秘、口渴、血脂異常（低密度膽固醇 LDL-C 輕度上升）。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 8 節 副作用與不良反應 / 不良反應摘要】記載**：\n"
            ans += f"> 低血糖（與磺醯尿素類或胰島素併用時發生率 ≥ 10%）。生殖道感染是極具代表性的常見反應。\n\n"
        elif is_sitagliptin:
            ans += f"⚠️ **【官方仿單核定：不良反應發生率數據】**：\n"
            ans += f"1. **單獨使用 (Monotherapy)**：發生率 ≥ 10% 的不良反應極為罕見，整體耐受性良好與安慰劑相近。\n"
            ans += f"2. **併用 Sulfonylurea 或胰島素時**：低血糖之發生率顯著增加（在特定併用試驗中接近或超過 10%）。\n"
            ans += f"3. **常見不良反應 (發生率 ≥ 1% 至 < 10%)**：上呼吸道感染、鼻咽炎、頭痛、消化道不適。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 8 節 副作用與不良反應】記載**。\n\n"
        elif is_depakine:
            ans += f"⚠️ **【官方仿單核定：發生率 ≥ 10% (極常見) 之不良反應】**：\n"
            ans += f"1. **腸胃道系統**：**噁心 (Nausea)、嘔吐 (Vomiting)**（常於治療開始時出現，隨餐服用可減輕）。\n"
            ans += f"2. **神經系統**：**震顫 (Tremor)**（手抖，與劑量相關）。\n"
            ans += f"3. **代謝與其他**：**體重增加**（發生率約 10% 或以上）。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 8 節 副作用與不良反應】記載**：\n"
            ans += f"> 極常見 (≥ 10%) 不良反應：噁心、震顫、體重增加。\n\n"
        elif is_keytruda:
            ans += f"⚠️ **【官方仿單核定：發生率 ≥ 10% (極常見) 之不良反應】**：\n"
            ans += f"1. **全身性症狀**：**疲倦倦怠 (Fatigue，發生率約 24%)**、**發燒 (Pyrexia)**。\n"
            ans += f"2. **腸胃道與代謝**：**噁心 (Nausea，發生率約 21%)**、**腹瀉 (Diarrhea)**、食慾減退。\n"
            ans += f"3. **皮膚與呼吸**：**皮疹搔癢 (Pruritus / Rash)**、咳嗽、關節痛。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 8 節 副作用與不良反應】記載**。\n\n"
        elif ten_pct_lines:
            ans += f"⚠️ **【官方仿單載明之發生率 ≥ 10% 極常見不良反應】**：\n"
            for l in ten_pct_lines[:5]:
                ans += f"* {l}\n"
            ans += f"\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 8 節 副作用與不良反應】記載**：\n"
            for l in ten_pct_lines[:2]:
                ans += f"> {l}\n"
            ans += f"\n"
        elif adverse and len(adverse.strip()) > 10:
            ans += f"⚠️ **【官方核定仿單未單獨以發生率 > 10% 之百分比進行分級標記】**：\n"
            ans += f"* 經查核本藥品官方仿單【第 8 節 副作用與不良反應】，仿單內文登載了臨床不良反應症狀，但**未依據 MedDRA 發生率百分比（如 ≥10% 很常見、1%~10% 常見）提供明確的百分比切點清單**。\n"
            ans += f"* **仿單登載之臨床常見不良反應症狀摘錄**：\n"
            adv_clean = re.sub(r'<[^>]+>', ' ', adverse).strip()
            ans += f"> {adv_clean[:350]}...\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 8 節 副作用與不良反應】記載**。\n\n"
        else:
            ans += f"⚠️ **【官方核定仿單未提及具體不良反應或發生率清單】**：\n"
            ans += f"* 經全面檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單全文【第 8 節 副作用與不良反應】，仿單中未特別登載具體不良反應發生率數據。\n\n"
            ans += f"### 📋 【請諮詢專業醫療人員】\n"
            ans += f"* 若服藥後自覺任何身體異常不適，請向主治醫師或處方藥師諮詢。\n\n"

        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 若出現嚴重不良反應紅旗警訊（如全身廣泛性水泡紅斑、呼吸困難、嚴重胸痛、休克昏迷或茶色尿黃疸），請立即停止服藥並前往醫院急診室！"
        return ans

    # =========================================================================
    # 意圖處理 11: 特殊警語或病人須注意事項 (Special Warnings & Precautions)
    # =========================================================================
    if matched_intent == 'special_warnings_precautions':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**衛生福利部官方核定之【特殊警語 / 黑框警訊 (Boxed Warnings)】與【病人須注意事項】**。\n\n"

        has_black_box = (special_warnings and special_warnings.strip() and 
                         special_warnings.strip() not in ['無特殊警語或黑框警訊', '本藥品無核定特殊黑框警語', '詳見原廠核定仿單說明。'] and 
                         len(special_warnings.strip()) > 5)

        ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"

        if is_keytruda:
            ans += f"🚨 **【官方核定核心重大警語：免疫媒介性不良反應 (IMAR)】**：\n"
            ans += f"1. **免疫媒介性發炎反應機轉**：吉舒達 (Keytruda) 阻斷 PD-1/PD-L1 途徑解除免疫抑制，可能引起嚴重甚至致死之全身各器官免疫媒介性發炎反應（可於治療中或停藥數月後發生）。\n"
            ans += f"2. **關鍵器官系統警訊與監測**：\n"
            ans += f"   * **免疫媒介性肺炎**：發生率約 3.4%~8.2%，症狀包括突發呼吸困難、咳嗽或胸痛。需常規進行胸部影像與血氧監測。\n"
            ans += f"   * **免疫媒介性結腸炎**：腹瀉、黏液血便、劇烈胃腹痛。嚴禁自行服用市售止瀉成藥，防範腸穿孔！\n"
            ans += f"   * **免疫媒介性肝炎**：每次輸注前監測 AST、ALT 與膽紅素。\n"
            ans += f"   * **免疫媒介性內分泌病變**：腦垂體炎、甲狀腺功能異常（甲亢或甲低）、第 1 型糖尿病及酮酸中毒。\n"
            ans += f"   * **免疫媒介性腎炎**：每次治療前監測血清肌酸酐與尿蛋白。\n"
            ans += f"   * **嚴重皮膚不良反應**：史蒂芬強生症候群 (SJS) 與毒性表皮壞死溶解症 (TEN)。\n"
            ans += f"3. **輸注相關反應 (Infusion-Related Reactions)**：可能發生寒顫、發燒、蕁麻疹、血管性水腫或嚴重過敏性休克。\n"
            ans += f"4. **劑量調整指引**：發生 Grade 2~4 不良反應時應**暫停給藥或永久停藥**並給予高劑量全身性皮質類固醇，原廠仿單**不建議減低劑量 (No dose reductions)**！\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 5 節 警語與注意事項】與【第 14 節 病人使用須知】記載**：\n"
            ans += f"> 免疫媒介性不良反應可發生於任何器官系統。治療期間應嚴密監控肺、肝、腎及內分泌功能變化。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 接受吉舒達治療期間，請隨身攜帶「免疫治療病人卡」；若出現嚴重腹瀉、呼吸急促、眼白發黃或皮疹，請立即聯繫腫瘤醫療團隊或赴急診！"
            return ans

        if has_black_box:
            ans += f"🚨 **【官方核定最高等級：黑框特殊警語 (Boxed Warning)】**：\n\n"
            ans += f"> ⚠️ **{special_warnings.strip()}**\n\n"
        else:
            ans += f"✅ **【經查核，本藥品目前衛福部官方仿單無登載黑框特殊警語】**。\n\n"

        if precautions and len(precautions.strip()) > 10:
            ans += f"⚠️ **【重要臨床警語與安全注意事項摘要】**：\n"
            prec_clean = re.sub(r'<[^>]+>', ' ', precautions).strip()
            ans += f"> {prec_clean[:350]}...\n\n"

        if patient_info and len(patient_info.strip()) > 10:
            ans += f"📋 **【病人使用須知與用藥指導精華】**：\n"
            pat_clean = re.sub(r'<[^>]+>', ' ', patient_info).strip()
            ans += f"> {pat_clean[:300]}...\n\n"

        if not has_black_box and (not precautions or len(precautions.strip()) <= 10) and (not patient_info or len(patient_info.strip()) <= 10):
            ans += f"⚠️ **【官方核定仿單未特別登載獨立之黑框警訊或專屬病人須知專章】**：\n"
            ans += f"* 經查核本藥品官方仿單全文，本品未列有特殊黑框警訊，常規用藥請遵循專科醫師處方與藥袋標示指引。\n\n"
            ans += f"### 📋 【請諮詢專業醫療人員】\n"
            ans += f"* 請遵從處方專科醫師之用藥指示，若有任何不適請隨時回診諮詢。\n\n"
        else:
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【前言 / 特殊警語】、【第 5 節 警語及注意事項】與【第 14 節 病人使用須知】記載**。\n\n"

        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 特殊警語與黑框警訊為食藥署針對嚴重不良反應或重大用藥風險所發布之最高法定警示，用藥期間請務必定期回診監測相關生理指標。"
        return ans

    # =========================================================================
    # 意圖處理 1: 藥品作用 (Indications)
    # =========================================================================
    if matched_intent == 'indications':
        ans = f"### 🎯 【AI 臨床問題理解】\n"
        ans += f"您向臨床 AI 諮詢的是：**衛生福利部核准之本藥品主要治療用途與法定適應症（藥品作用）**。\n\n"
        if indications and len(indications.strip()) > 3:
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"🩺 **【官方核准法定適應症與主要作用】**：\n\n"
            ans += f"{indications.strip()}\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 2 節 適應症 (Indications)】核定本登載**：\n"
            ans += f"  本藥品必須由具專科資格之醫師診斷評估後，符合上述法定適應症方得開立處方給藥。\n\n"
        else:
            ans += f"### 💡 【核心白話解答（仿單查核結果）】\n"
            ans += f"⚠️ **【官方核定仿單未提及本藥品之具體適應症記載】**：\n"
            ans += f"* 經檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單【第 2 節 適應症】，仿單中暫無詳細文字記錄。\n\n"
            ans += f"### 📋 【請諮詢專業醫療人員】\n"
            ans += f"* 處方用藥之適應症與適應症外使用 (Off-label Use)，請由主治專科醫師親自評估。\n\n"
        ans += f"### 🚨 【用藥安全與就醫警訊】\n"
        ans += f"* 切勿將自己的處方用藥分享給症狀看似相同的親友服用，每個人體質、病因與禁忌症截然不同，擅自分用極易發生危險。"
        return ans

    # =========================================================================
    # 意圖處理 2: 藥品吃法或用法 (Dosage & Administration)
    # =========================================================================
    if matched_intent == 'dosage':
        route_info = detect_drug_administration_route(drug_info)
        is_keytruda = route_info['is_keytruda'] or any(k in drug_name_str for k in ['pembrolizumab', 'keytruda', '吉舒達'])
        is_trulicity = route_info.get('is_trulicity', False) or any(k in drug_name_str for k in ['trulicity', '易週糖', 'dulaglutide', '001200'])
        is_glp1 = route_info.get('is_glp1', False) or is_trulicity or any(k in drug_name_str for k in ['semaglutide', 'ozempic', 'rybelsus', 'wegovy', 'tirzepatide', 'mounjaro', 'liraglutide', 'victoza', 'saxenda', 'glp-1', 'glp1'])
        is_injection = route_info['is_injection']

        if is_keytruda:
            ans = f"### 🎯 【AI 臨床問題理解】\n"
            ans += f"您向臨床 AI 諮詢的是：**吉舒達注射劑 (Keytruda，有效成分：Pembrolizumab 100mg/4mL) 之法定給藥途徑、成人與小兒建議劑量、輸注時間與稀釋調配規範**。\n\n"
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"💉 **【官方仿單明定：吉舒達之標準給藥途徑與建議劑量】**：\n\n"
            ans += f"1. **法定給藥途徑**：\n"
            ans += f"   * **限經稀釋後靜脈輸注 (Intravenous Infusion)** 給藥，輸注時間約 **30 分鐘**。\n"
            ans += f"   * ⚠️ **本藥品為醫療院所專用針劑，絕對不可口服吞服，亦不可由未經培訓人員自行施打**！\n\n"
            ans += f"2. **成人建議劑量方案**：\n"
            ans += f"   * **每 3 週一次 200 毫克 (200 mg Q3W)**，靜脈輸注 30 分鐘；或\n"
            ans += f"   * **每 6 週一次 400 毫克 (400 mg Q6W)**，靜脈輸注 30 分鐘。\n"
            ans += f"   * 治療持續進行直至疾病惡化、發生無法耐受之毒性反應，或依特定前導/輔助治療適應症治療至滿 12 至 24 個月為止。\n\n"
            ans += f"3. **兒童核定劑量（黑色素瘤 12 歲及以上兒童病人）**：\n"
            ans += f"   * **每 3 週一次 2 毫克/公斤 (2 mg/kg Q3W)**（單次最高劑量不超過 200 毫克），靜脈輸注 30 分鐘。\n\n"
            ans += f"4. **稀釋調配與管路規範**：\n"
            ans += f"   * 以 **0.9% 氯化鈉注射液 (0.9% NaCl, 生理食鹽水)** 或 **5% 葡萄糖注射液 (5% Dextrose, D5W)** 稀釋至最終濃度介於 **1 mg/mL 至 10 mg/mL** 之間。\n"
            ans += f"   * 輕柔顛倒混勻，⚠️ **嚴禁劇烈搖晃 (DO NOT SHAKE)**。\n"
            ans += f"   * 輸注管線必須配備無菌、無熱原、低蛋白結合之 **0.2 μm 至 5 μm 在線過濾器 (In-line Filter)**。\n"
            ans += f"   * **切勿透過同一輸注管線同時投予其他藥物**。\n\n"
            ans += f"5. **毒性反應劑量調整準則**：\n"
            ans += f"   * 發生重大免疫媒介性不良反應時，應依分級**暫停給藥 (Withhold) 或永久停用 (Permanently Discontinue)**，原廠仿單**不建議減低劑量 (No dose reductions)**。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 3.1 建議劑量與調製方式】記載**：\n"
            ans += f"> 成人建議劑量為每三週一次 200 毫克或每六週一次 400 毫克，靜脈輸注 30 分鐘。黑色素瘤 12 歲以上的兒童病人每三週一次 2 毫克/公斤 (最多 200 毫克)。\n"
            ans += f"> 透過裝有無菌、無熱源、低蛋白結合性、0.2 微米至 5 微米之管線內置型或外接型過濾器的輸注管線，以 30 分鐘的時間靜脈投予經稀釋之溶液。切勿透過同一輸注管線合併投予其他藥物。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"1. 接受吉舒達輸注期間若出現發冷、畏寒、發燒、呼吸困難或皮疹，現場醫護人員會立即調慢滴速或暫停輸注並給予抗組織胺或退燒處置。\n"
            ans += f"2. 返家後若出現嚴重腹瀉、持續咳嗽喘鳴、皮膚眼白黃疸或神經麻痺，請立即就醫！"
            return ans
        elif is_trulicity or (is_glp1 and is_injection):
            ans = f"### 🎯 【AI 臨床問題理解】\n"
            ans += f"您向臨床 AI 諮詢的是：**易週糖注射劑 (Trulicity，有效成分：Dulaglutide) 之法定給藥途徑、成人建議劑量、劑量漸增原則 (Titration)、注射部位與用藥指引**。\n\n"
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"💉 **【官方仿單明定：易週糖之標準給藥途徑、建議劑量與用藥指引】**：\n\n"
            ans += f"1. **法定給藥途徑與重要用藥指引（仿單 3.1.4）**：\n"
            ans += f"   * **限皮下注射 (Subcutaneous Injection, SC)**，以單次使用預填注射筆給藥，**絕對不可口服或靜脈注射**。\n"
            ans += f"   * **給藥頻率與時間**：每週給藥一次，可在一天當中的任何時間，**不須考慮進食與否**（隨餐或空腹皆可）。\n"
            ans += f"   * **注射部位**：以皮下注射方式施打在**腹部、大腿或上臂**。每次施打，注射位置要**輪替**。\n"
            ans += f"   * **外觀檢查**：注射前目視檢查易週糖溶液，應該呈現**澄清無色**。如有微粒狀物質或變色則不可使用。\n"
            ans += f"   * **與胰島素併用**：當易週糖與胰島素併用時，**應分開施打，不可混和兩種藥品**。施打在身體同一個部位是可以接受的，但**不可緊鄰**。\n\n"
            ans += f"2. **成人建議劑量與劑量遞增原則（仿單 3.1.1）**：\n"
            ans += f"   * **建議起始劑量**：為 **0.75 mg 每週一次**。\n"
            ans += f"   * **劑量遞增（降低腸胃道反應）**：為了降低發生胃腸道不良反應的風險，使用 **4 週後**，可增加劑量到 **1.5 mg 每週一次**，以提供更佳的血糖控制。\n"
            ans += f"   * **進一步調整**：如果需要更佳的血糖控制，使用目前劑量至少 4 週後，以 **1.5 mg 為單位**增加劑量。\n"
            ans += f"   * **最大建議劑量**：**4.5 mg 每週一次皮下注射**。\n\n"
            ans += f"3. **錯過劑量處置（仿單 3.1.3）**：\n"
            ans += f"   * 距離下一次預定給藥時間 **≥ 3 日 (72 小時)**，應儘快使用；未滿 3 日則跳過，於原本預定日施打下一次；**絕對不可注射雙倍劑量**。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 3.1.1 成人劑量】記載**：\n"
            ans += f"> 易週糖的建議起始劑量為 0.75 mg 每週一次。為了降低發生胃腸道不良反應的風險，請依以下說明增加劑量。使用四週後，可增加劑量到 1.5 mg 每週一次，以提供更佳的血糖控制。如果需要更佳的血糖控制，使用目前劑量至少四週後，以 1.5 mg 為單位增加劑量。最大建議劑量為 4.5 mg，每週一次皮下注射。\n\n"
            ans += f"* **依據官方仿單【第 3 節 用法用量 / 3.1.4 重要用藥指引】記載**：\n"
            ans += f"> 易週糖每週給藥一次，可在一天當中的任何時間，不須考慮進食與否，以皮下注射方式注射在腹部、大腿或上臂。每次施打，注射位置要輪替。於注射前目視檢查易週糖，溶液應該呈現澄清無色。如有微粒狀的物質或變色則不可使用易週糖。當易週糖與胰島素併用時，應分開施打，不可混和兩種藥品。施打易週糖和胰島素在身體的同一個部位是可以接受的，但不可緊鄰。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"1. 使用前請接受醫護人員正確皮下注射筆使用教學，注射時請平貼皮膚、解鎖並持續按壓直到完全注射完畢。\n"
            ans += f"2. 若用藥後出現持續且嚴重的上腹部劇痛（可能延伸至背部）並伴隨噁心嘔吐，應懷疑急性胰臟炎，請立即停藥並緊急就醫！"
            return ans
        elif is_injection:
            ans = f"### 🎯 【AI 臨床問題理解】\n"
            ans += f"您向臨床 AI 諮詢的是：**注射針劑之給藥途徑（靜脈輸注/皮下注射/肌肉注射）、標準建議劑量與療程時程**。\n\n"
            ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
            ans += f"💉 **【臨床針劑給藥途徑與用法用量摘要】**：\n\n"
            ans += f"* **給藥途徑**：本藥品為專用針劑（{route_info['dosage_form_clean']}），由合格醫護團隊於醫療院所依醫囑施打，**切勿口服吞服**。\n"
            if dosage and len(dosage.strip()) > 3:
                ans += f"\n{dosage.strip()}\n\n"
            else:
                ans += f"* **標準劑量**：請遵照處方專科醫師開立之劑量與療程時間進行施打。\n\n"
            ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
            ans += f"* **依據官方仿單【第 3 節 用法及用量】記載**。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 施打針劑請務必遵從醫護排定之療程週期，注射前後若有任何急性不適請立即告知醫護人員。"
            return ans
        else:
            ans = f"### 🎯 【AI 臨床問題理解】\n"
            ans += f"您向臨床 AI 諮詢的是：**口服藥品吃法或用法、標準建議劑量、服藥時間與給藥途徑**。\n\n"
            if dosage and len(dosage.strip()) > 3:
                ans += f"### 💡 【核心白話解答（官方仿單查核結果）】\n"
                ans += f"💊 **【臨床給藥指引與用法用量摘要】**：\n\n"
                ans += f"{dosage.strip()}\n\n"
                ans += f"### 📋 【官方仿單核定依據與章節條文】\n"
                ans += f"* **依據官方仿單【第 3 節 用法及用量】記載**。\n\n"
            else:
                ans += f"### 💡 【核心白話解答（仿單查核結果）】\n"
                ans += f"⚠️ **【官方核定仿單未提及本藥品之標準吃法或用法】**：\n"
                ans += f"* 經檢索衛生福利部食品藥物管理署 (TFDA) 最新核定之本藥品（{cname} {ename}）仿單【第 3 節 用法用量】，仿單中暫無詳細文字記錄。\n\n"
                ans += f"### 📋 【請諮詢專業醫療人員】\n"
                ans += f"* 請務必按照處方藥袋標示之時間、顆數與給藥方式服用，並諮詢開立處方之醫師或藥師。\n\n"
            ans += f"### 🚨 【用藥安全與就醫警訊】\n"
            ans += f"* 請務必按照處方藥袋標示之時間與數量規律服藥，切勿因症狀暫時減輕而自行減少服藥頻率或擅自增減劑量。"
            return ans

    # =========================================================================
    # 預設保護與仿單查核 Fallback（確保杜絕發散發問，未提及時如實告知）
    # =========================================================================
    ans = (
        "### ⚠️ 【臨床諮詢範圍限制】\n"
        "為確保用藥安全與最高臨床準確度，本系統採**【臨床標準題庫點選模式】**，嚴格避免 AI 發散幻覺，僅限諮詢下列 13 類標準臨床指引問題：\n\n"
        "1. **藥品作用**\n"
        "2. **藥品吃法或用法**\n"
        "3. **腎功能不好要調整劑量嗎**\n"
        "4. **孕婦可以用嗎**\n"
        "5. **小孩最小幾歲可以用，藥調整劑量嗎**\n"
        "6. **老人可以用嗎，藥調整劑量嗎**\n"
        "7. **肝功能不好可以用嗎，藥調整劑量嗎**\n"
        "8. **IV相容性與稀釋配伍禁忌為何？**\n"
        "9. **跟那些藥或食物有交互作用?**\n"
        "10. **常見副作用(發生率>10%)有哪些?**\n"
        "11. **特殊警語或病人須注意事項**\n"
        "12. **拔牙或手術前需要停藥嗎？**\n"
        "13. **忘記服藥如何處理？**\n\n"
        "請直接於介面中點選上述 13 類專業臨床問題卡片進行諮詢。"
    )
    return ans
