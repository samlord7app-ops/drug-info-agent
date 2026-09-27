import React, { useState } from 'react';

export default function SmartPillbox() {
  const [drugName, setDrugName] = useState('bokey');
  const [selectedQuestion, setSelectedQuestion] = useState(10);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([
    '💡 [待命] 請選擇您想諮詢的臨床問題（13選1）...'
  ]);
  const [resultData, setResultData] = useState(null);

  // 13 類標準臨床諮詢問題清單
  const questions = [
    { id: 1, text: '01 藥品作用' },
    { id: 2, text: '02 藥品吃法或用法' },
    { id: 3, text: '03 腎功能不好要調整劑量嗎' },
    { id: 4, text: '04 孕婦可以用嗎' },
    { id: 5, text: '05 小孩最小幾歲可以用，要調整劑量嗎' },
    { id: 6, text: '06 老人可以用嗎，要調整劑量嗎' },
    { id: 7, text: '07 肝功能不好可以用嗎，要調整劑量嗎' },
    { id: 8, text: '08 IV相容性與稀釋配伍禁忌為何？' },
    { id: 9, text: '09 跟那些藥或食物有交互作用？' },
    { id: 10, text: '10 常見副作用(發生率>10%)有哪些?' },
    { id: 11, text: '11 特殊警語或病人須注意事項' },
    { id: 12, text: '12 拔牙或手術前需要停藥嗎？' },
    { id: 13, text: '13 忘記服藥如何處理？' },
  ];

  // 點擊問題發送請求
  const handleAskQuestion = async (qId, qText) => {
    if (!drugName.trim()) {
      alert('請先輸入藥品名稱！');
      return;
    }

    setSelectedQuestion(qId);
    setLoading(true);
    setResultData(null);

    const targetUrl = 'https://drug-info-agent.onrender.com/api/drug_insert';

    setLogs([
      '🚀 [啟動] 準備發送請求至專屬 AI 代理人...',
      `🌐 [連線] 目標網址：${targetUrl}`,
      `🔍 [資料] 藥品：「${drugName}」 | 類別：「${qText}」`,
      '⏳ [分析] 雲端正在深度研讀衛福部核定仿單全章節，請稍候...'
    ]);

    try {
      const response = await fetch(targetUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          drug_name: drugName.trim(),
          category: qText,
        }),
      });

      const data = await response.json();

      if (!data || (!data.success && !data.patient_answer && !data.answer)) {
        setLogs(prev => [
          ...prev.slice(0, 3),
          `❌ [錯誤] 查詢失敗：${data.error || '未找到相符之藥品仿單'}`
        ]);
        setLoading(false);
        return;
      }

      setLogs([
        '🚀 [啟動] 準備發送請求至專屬 AI 代理人...',
        `🌐 [連線] 目標網址：${targetUrl}`,
        `🔍 [資料] 藥品：「${drugName}」 | 類別：「${qText}」`,
        '📄 [解析] 成功接收來自伺服器的 JSON 資料！',
        '✨ [完成] 分析完畢，請查閱下方報告與連結。'
      ]);

      setResultData(data);
    } catch (err) {
      console.error(err);
      setLogs(prev => [
        ...prev.slice(0, 3),
        `❌ [連線異常] 無法連線至伺服器：${err.message}`
      ]);
    } finally {
      setLoading(false);
    }
  };

  // 語音播報功能（自動過濾 Markdown 標記，朗讀清晰）
  const handleVoiceSpeak = (lang = 'zh-TW') => {
    const rawAnswer = resultData?.patient_answer || resultData?.answer;
    if (!rawAnswer) return;

    if (!('speechSynthesis' in window)) {
      alert('您的瀏覽器不支援語音播放功能');
      return;
    }

    window.speechSynthesis.cancel();

    // 過濾 Markdown 語法符號與 Emoji
    const cleanText = rawAnswer
      .replace(/###/g, '')
      .replace(/[*_`>#-]/g, '')
      .replace(/[\u{1F300}-\u{1F6FF}]/gu, '')
      .replace(/\n+/g, '，')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.95;
    utterance.lang = lang === 'en-US' ? 'en-US' : 'zh-TW';
    window.speechSynthesis.speak(utterance);
  };

  // 取得有效 PDF 連結
  const pdfLink = resultData?.pdf_url || resultData?.download_insert_pdf_url || resultData?.insert_pdf_url;
  const insertLink = resultData?.insert_url || resultData?.e_insert_url || resultData?.official_detail_url;

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 space-y-6 font-sans text-slate-800 bg-slate-50 min-h-screen">
      
      {/* 1. 藥名輸入區塊 */}
      <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 space-y-3">
        <div className="flex items-center gap-2 text-slate-900 font-bold text-base sm:text-lg">
          <span className="text-blue-600 text-xl">💊</span>
          <span>智慧用藥諮詢與官方仿單查詢系統</span>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={drugName}
            onChange={(e) => setDrugName(e.target.value)}
            placeholder="請輸入藥品名稱（如：bokey、trulicity、panadol）"
            className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm font-medium"
          />
          <button
            onClick={() => handleAskQuestion(selectedQuestion, questions.find(q => q.id === selectedQuestion)?.text || '')}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-xl transition-colors shadow-sm"
          >
            查詢
          </button>
        </div>
      </div>

      {/* 2. 13 類專業臨床問題選單 (13選1) */}
      <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 space-y-4">
        <div className="flex items-center gap-2 text-slate-900 font-bold text-sm sm:text-base">
          <span>📋</span>
          <span>請選擇想詢問的問題 (13選1) :</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {questions.map((q) => {
            const isSelected = selectedQuestion === q.id;
            return (
              <button
                key={q.id}
                onClick={() => handleAskQuestion(q.id, q.text)}
                className={`p-3 rounded-xl border text-sm font-medium text-left transition-all ${
                  isSelected
                    ? 'border-blue-500 bg-blue-600 text-white shadow-sm'
                    : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
                } ${q.id === 13 ? 'col-span-1 sm:col-span-2 lg:col-span-2' : ''}`}
              >
                {q.text}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. 終端連線日誌 (Terminal Console) */}
      <div className="bg-slate-900 rounded-2xl p-4 text-slate-200 font-mono text-xs sm:text-sm shadow-md border border-slate-800 space-y-2">
        <div className="flex items-center gap-2 text-slate-400 pb-1 border-b border-slate-800 text-xs">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span>
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span>
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
          <span className="ml-2 font-semibold text-slate-300">連線監控面板</span>
        </div>
        <div className="space-y-1 pt-1">
          {logs.map((line, idx) => (
            <div key={idx} className="leading-relaxed">
              {line}
            </div>
          ))}
        </div>
      </div>

      {/* 4. 結果卡片 */}
      {resultData && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-5">
          
          {/* 工具列：語音播報與 PDF 按鈕 */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
            {/* 語音播報按鈕 */}
            <div className="flex items-center gap-2 text-sm text-slate-700">
              <span className="font-bold flex items-center gap-1 text-slate-800">
                🔊 語音播報：
              </span>
              <button
                onClick={() => handleVoiceSpeak('zh-TW')}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
              >
                🗣 中文
              </button>
              <button
                onClick={() => handleVoiceSpeak('zh-TW')}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
              >
                🗣 台語
              </button>
              <button
                onClick={() => handleVoiceSpeak('en-US')}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
              >
                🗣 英文
              </button>
            </div>

            {/* 仿單 PDF 按鈕 (綠色主按鈕) */}
            <div className="flex items-center gap-2">
              <a
                href={pdfLink || insertLink || 'https://mcp.fda.gov.tw/'}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs sm:text-sm font-semibold inline-flex items-center gap-2 shadow-sm transition-all"
              >
                <span>📄</span>
                <span>
                  {pdfLink 
                    ? `開啟/下載「${resultData.drug_name || drugName}」仿單 PDF` 
                    : `前往衛福部「藥品仿單查詢平台」`}
                </span>
              </a>

              {/* 線上電子仿單次要按鈕 */}
              {insertLink && (
                <a
                  href={insertLink}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-xl text-xs sm:text-sm font-semibold inline-flex items-center gap-1.5 transition-all"
                >
                  <span>🌐</span>
                  <span>線上電子仿單</span>
                </a>
              )}
            </div>
          </div>

          {/* 提示訊息框 */}
          {pdfLink ? (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs sm:text-sm leading-relaxed flex items-center gap-2">
              <span>✅</span>
              <span>已成功取得衛福部食藥署核定之<strong>「{resultData.drug_name || drugName}」官方 PDF 仿單</strong>，點擊上方綠色按鈕即可直接開啟查閱。</span>
            </div>
          ) : (
            <div className="p-3.5 bg-blue-50 border border-blue-200 text-blue-800 rounded-xl text-xs sm:text-sm leading-relaxed flex items-center gap-2">
              <span>ℹ️</span>
              <span>提示：若 AI 尚未能獲取 PDF 連結，請點擊上方按鈕前往「藥品仿單查詢平台」，輸入「{drugName}」即可輕鬆查閱官方仿單。</span>
            </div>
          )}

          {/* 白話版衛教解答內容 */}
          <div className="p-2 space-y-3 text-slate-800 leading-relaxed text-sm sm:text-base whitespace-pre-line">
            {resultData.patient_answer || resultData.answer}
          </div>
        </div>
      )}

    </div>
  );
}
