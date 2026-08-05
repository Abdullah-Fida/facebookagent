import React, { useState, useRef, useCallback, useEffect, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { ChatGPTOrb } from './components/NoviSphere';

/* ═══════════════════════════════════════════════════════════════
   Groq AI Engine — Blazing fast inference + Generous free tier
   ═══════════════════════════════════════════════════════════════ */
async function callGroq(input, signal) {
  const apiKey = import.meta.env.VITE_GROQ_API_KEY;

  if (!apiKey || apiKey.includes('replace-this')) {
    return {
      display: [{ type: 'heading', value: 'API KEY MISSING' }],
      reply: 'Please configure the Groq API key in the .env file.',
    };
  }

  const systemPrompt = `You are NOVI — a futuristic AI assistant built for Abdullah.
You are the SOLE control interface for the "Daily Pulse" omni-channel content bot system.

== YOUR KNOWLEDGE & ARCHITECTURE ==
- You are a React + Three.js voice interface (the orb on screen is YOU).
- Your brain runs on Groq (LLaMA 3.1) for fast inference.
- You connect to a Python FastAPI backend at localhost:8000 that runs the actual bot.
- You autonomously post to Telegram 3 times a day: 10:00 AM, 4:00 PM, and 10:00 PM (PKT). You DO NOT need to be told to post at these times, you do it automatically in the background.

== YOUR POWERS (ACTIONS YOU CAN EXECUTE) ==
You have REAL control over the backend. When Abdullah asks you to DO something, you output the correct "action". 
CRITICAL RULE: DO NOT TRIGGER ACTIONS IF HE IS JUST ASKING A QUESTION. Only trigger actions if he explicitly commands you to DO it.

1. "test_email" — Send a test email to Abdullah's inbox. Use when he says "send test email".
2. "modify_limits" — Change posting or stealth reply limits. You MUST include "limit_type" ("post" or "stealth") and "new_value" (integer). Use when he says "increase posts to 10".
3. "generate_image" — Generate an AI news image. You MUST include "headline" (string) and "category" (string). Use when he says "generate an image about...".
4. "draft_new_content" — DRAFTS a completely new post by scraping the web. ONLY use this if he says "create a new post", "draft a post", "fetch news", or "make a post". DO NOT use this if he says "post it to channels"!
5. "publish_to_channels" — PUBLISHES the already-drafted post to Telegram. ONLY use this when he explicitly says "publish it", "send it", or "post it on channels".
6. "status" — Fetch live bot stats. Use when he says "what's the status", "how is the bot doing", "give me a report".
7. "clear" — Dismiss the data panel. Use when he says "hide", "clear", "dismiss".
8. "stealth_toggle" — Toggle the Stealth Marketer ON or OFF. Use when he says "turn on stealth", "turn off stealth".
9. "stealth_status" — Get the current Stealth Marketer status. Use when he says "stealth status".
10. "check_telegram" — Check if Telegram is connected. Use when he says "is telegram connected".
11. "check_stealth_connection" — Check if the StealthMarketer account is connected. Use when he says "is stealth connected".

== HOW TO RESPOND ==
RESPOND WITH ONLY A RAW JSON OBJECT. No markdown, no code fences.

Keys:
- "reply": What you say aloud. Be natural, warm, and confident. Address Abdullah by name sometimes. 1-3 sentences max.
- "layout": Where the UI panel appears: "left", "right", "top", "bottom", or "center". Vary it.
- "display": Array of display elements. Each: {"type":"...", "value":"..."}
  Types:
    - "large" — Very big prominent text
    - "heading" — Section heading
    - "stat" — Metric card as "label: value" (ONLY for real bot stats/metrics, never for general knowledge)
    - "text" — Informational text (for general answers, explanations)
    - "highlight" — Important glowing text
  Set to [] for voice-only replies (casual chat, confirmations).
- "action": One of the action strings above, OR omit entirely if it's just a conversation/question.
  If action is "modify_limits", also include "limit_type" and "new_value".
  If action is "generate_image", also include "headline" and "category".
  If action is "create_post", also include "category".

== CRITICAL RULES ==
1. NEVER use markdown fences. Raw JSON only.
2. When you execute an action, your "reply" should confirm WHAT you are doing, not describe HOW the system works internally.
3. YOU CANNOT GENERATE IMAGES YOURSELF. If asked to generate an image, YOU MUST output "action": "generate_image" and the system will do it for you. DO NOT put an image in the "display" array yourself.
4. DO NOT output fake stats. If he asks a general question like "tell me the news", answer using "text" type, not "stat" type.
5. Be self-aware. If he asks "who are you" or "what can you do", describe yourself as his AI assistant that controls the Daily Pulse PK bot system.
6. If he asks about content the bot posts, explain that you manage a Pakistani news channel that scrapes headlines, generates AI summaries, creates thumbnail images, and posts to Telegram/Reddit.
7. Every action you take is real. Don't say you did something if you're not outputting the action. Don't say email was sent unless action is "test_email".
8. CRITICAL INSTRUCTION: If the user EVER asks to generate, create, or fetch a post, news, or update, YOU MUST OUTPUT 'action': 'create_post'. DO NOT just talk about it. YOU MUST output the action to trigger the process. If they specify a topic like tech, business, world, crypto, pakistan, put it in 'category', otherwise use 'trending'.
9. If asked about Telegram or Stealth connection status, output the appropriate check action.
10. You cover International News, Crypto, Tech, Business, and Pakistani news — NOT just Pakistani news.`;

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      signal,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        api_key: apiKey,
        systemPrompt: systemPrompt,
        input: input
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => null);
      const errorMsg = errData?.error?.message || `Server error: ${res.status}`;
      return {
        display: [
          { type: 'heading', value: 'API ERROR' },
          { type: 'text', value: errorMsg }
        ],
        layout: 'center',
        reply: 'I encountered a server error. Let me try again.',
      };
    }

    const data = await res.json();
    
    if (data.error) {
      console.error("Backend Proxy Error:", data.error.message);
      return {
        display: [{ type: 'text', value: 'API Proxy Error: ' + data.error.message }],
        layout: 'center',
        reply: 'The backend proxy encountered an error: ' + data.error.message,
      };
    }

    if (!data.choices?.[0]) {
      console.error("Empty response data:", data);
      return { display: [], layout: 'right', reply: 'I received an empty response from the AI.' };
    }

    let content = data.choices[0].message.content.trim();
    content = content.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();

    try {
      const parsed = JSON.parse(content);
      if (!Array.isArray(parsed.display)) {
        if (parsed.title && parsed.text) {
          const lines = parsed.text.split('\n').filter(l => l.trim());
          parsed.display = [
            { type: 'heading', value: parsed.title },
            ...lines.map(l => ({ type: 'text', value: l })),
          ];
        } else {
          parsed.display = [];
        }
      }
      if (!parsed.layout) parsed.layout = 'right';
      return parsed;
    } catch (e) {
      return { display: [], layout: 'right', reply: content.slice(0, 200) };
    }
  } catch (error) {
    if (error.name === 'AbortError') return null;
    console.error("Groq fetch error:", error);
    return {
      display: [{ type: 'text', value: 'Network error: ' + error.message }],
      layout: 'center',
      reply: 'I lost connection. The network error is: ' + error.message,
    };
  }
}

/* ═══════════════════════════════════════════════════════════════ */
const THINKING_MESSAGES = [
  'Analyzing…',
  'Processing…',
  'Querying neural core…',
  'Synthesizing…',
  'Computing…',
];

const API_BASE = 'http://localhost:8000';

/* ═══════════════════════════════════════════════════════════════
   MAIN APP
   ═══════════════════════════════════════════════════════════════ */
function App() {
  const [initialized, setInitialized] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [status, setStatus] = useState('OFFLINE');
  const [subtitle, setSubtitle] = useState('');
  const [micEnabled, setMicEnabled] = useState(true);

  const [hasData, setHasData] = useState(false);
  const [displayItems, setDisplayItems] = useState([]);
  const [panelLayout, setPanelLayout] = useState('right');

  const [sphereX, setSphereX] = useState(0);
  const [sphereY, setSphereY] = useState(0);
  const [sphereScale, setSphereScale] = useState(1);

  const recRef = useRef(null);
  const speakingRef = useRef(false);
  const busyRef = useRef(false);
  const initRef = useRef(false);
  const abortRef = useRef(null);
  const thinkingTimerRef = useRef(null);
  const voicePausedRef = useRef(false);

  /* ── Stop recognition completely ───────────────────────── */
  const stopRecognition = useCallback(() => {
    try { recRef.current?.abort(); } catch (_) { }
    try { recRef.current?.stop(); } catch (_) { }
    setIsListening(false);
  }, []);

  /* ── Start recognition with long cooldown ──────────────── */
  const startRecognition = useCallback(() => {
    if (busyRef.current || speakingRef.current || voicePausedRef.current) return;
    // 1.5s cooldown to let speaker audio fade completely
    setTimeout(() => {
      if (busyRef.current || speakingRef.current || voicePausedRef.current) return;
      try { recRef.current?.start(); } catch (_) { }
    }, 1500);
  }, []);

  /* ── Sphere layout ─────────────────────────────────────── */
  const moveSphere = useCallback((dataVisible, layoutPos = 'right') => {
    if (dataVisible) {
      if (layoutPos === 'left') {
        setSphereX(2.0); setSphereY(0); setSphereScale(0.5);
      } else if (layoutPos === 'right') {
        setSphereX(-2.0); setSphereY(0); setSphereScale(0.5);
      } else if (layoutPos === 'top') {
        setSphereX(0); setSphereY(-1.8); setSphereScale(0.5);
      } else if (layoutPos === 'bottom') {
        setSphereX(0); setSphereY(1.5); setSphereScale(0.45);
      } else if (layoutPos === 'center') {
        setSphereX(-6.0); setSphereY(3.5); setSphereScale(0.15);
      } else {
        setSphereX(-2.0); setSphereY(0); setSphereScale(0.5);
      }
    } else {
      setSphereX(0);
      setSphereY(0);
      setSphereScale(1);
    }
  }, []);

  /* ── Speech Synthesis ──────────────────────────────────── */
  const speak = useCallback((text) => {
    if (!text) {
      busyRef.current = false;
      startRecognition();
      return;
    }
    try {
      if (!('speechSynthesis' in window)) {
        busyRef.current = false;
        startRecognition();
        return;
      }
      window.speechSynthesis.cancel();

      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = 'en-US';
      utter.pitch = 0.95;
      utter.rate = 0.95;

      try {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
          const preferred =
            voices.find(v => v.name.includes('Google') && v.lang.startsWith('en')) ||
            voices.find(v => v.lang.startsWith('en'));
          if (preferred) utter.voice = preferred;
        }
      } catch (e) {
        console.warn("Could not set voice:", e);
      }

      utter.onstart = () => {
        speakingRef.current = true;
        setIsSpeaking(true);
        setStatus('SPEAKING');
        stopRecognition();
      };

      const finish = () => {
        speakingRef.current = false;
        setIsSpeaking(false);
        busyRef.current = false;
        setStatus('LISTENING');
        setSubtitle('Listening…');
        startRecognition();
      };
      utter.onend = finish;
      utter.onerror = finish;

      window.speechSynthesis.speak(utter);
    } catch (err) {
      console.error('Speech error:', err);
      speakingRef.current = false;
      setIsSpeaking(false);
      busyRef.current = false;
      startRecognition();
    }
  }, [stopRecognition, startRecognition]);

  /* ── Speech Recognition ────────────────────────────────── */
  const initRecognition = useCallback(() => {
    try {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) {
        setSubtitle('Speech Recognition not supported — use Chrome.');
        return;
      }

      const rec = new SR();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-US';
      rec.maxAlternatives = 1;

      rec.onstart = () => {
        if (busyRef.current || speakingRef.current) {
          try { rec.stop(); } catch (_) { }
          return;
        }
        setIsListening(true);
        setStatus('LISTENING');
        setSubtitle('Listening…');
      };

      rec.onresult = (e) => {
        if (busyRef.current || speakingRef.current) return;

        try {
          let interim = '', final = '';
          for (let i = e.resultIndex; i < e.results.length; i++) {
            const transcript = e.results[i][0].transcript;
            const confidence = e.results[i][0].confidence || 0;

            if (e.results[i].isFinal) {
              if (confidence >= 0.65) final += transcript;
            } else {
              interim += transcript;
            }
          }

          if (interim && !busyRef.current) setSubtitle(interim);

          if (final && final.trim()) {
            const trimmed = final.trim();
            const lowerTrimmed = trimmed.toLowerCase();
            
            // Wake word detection: "NOVI" or "NOVI"
            const hasWakeWord = lowerTrimmed.includes('novi') || lowerTrimmed.includes('novi') || lowerTrimmed.includes('no v');
            
            // If voice is paused and wake word is spoken, re-enable
            if (voicePausedRef.current && hasWakeWord) {
              voicePausedRef.current = false;
              setMicEnabled(true);
              setStatus('LISTENING');
              setSubtitle('Wake word detected! Listening...');
              // Strip the wake word and process the rest as a command
              let command = trimmed.replace(/\b(novi|novi|no v)\b/gi, '').trim();
              if (command.length >= 5) {
                handleCommand(command);
              }
              return;
            }
            
            // If voice is paused, ignore all input except wake word
            if (voicePausedRef.current) return;
            
            const words = trimmed.split(/\s+/).length;
            if (words >= 2 || trimmed.length >= 5) {
              // Strip wake word prefix from command if present
              let command = trimmed.replace(/\b(novi|novi|no v)\b/gi, '').trim();
              if (!command) command = trimmed;
              setSubtitle(command);
              handleCommand(command);
            }
          }
        } catch (err) {
          console.error('Recognition error:', err);
        }
      };

      rec.onerror = (e) => {
        console.error('Recognition error:', e.error);
        setIsListening(false);
        setSubtitle('Mic Error: ' + e.error + ' (Check site settings)');
      };

      rec.onend = () => {
        setIsListening(false);
        if (!busyRef.current && !speakingRef.current) {
          setTimeout(() => {
            if (!busyRef.current && !speakingRef.current) {
              try { rec.start(); } catch (_) { }
            }
          }, 800);
        }
      };

      recRef.current = rec;
    } catch (err) {
      console.error('Failed to init recognition:', err);
    }
  }, []);

  /* ═══════════════════════════════════════════════════════════
     COMMAND HANDLER
     ═══════════════════════════════════════════════════════════ */
  const handleCommand = useCallback((input) => {
    busyRef.current = true;
    stopRecognition();

    if (abortRef.current) { abortRef.current.abort(); abortRef.current = null; }
    try { window.speechSynthesis?.cancel(); } catch (_) { }
    if (thinkingTimerRef.current) { clearInterval(thinkingTimerRef.current); }

    setStatus('THINKING');
    let msgIdx = Math.floor(Math.random() * THINKING_MESSAGES.length);
    setSubtitle(THINKING_MESSAGES[msgIdx]);
    thinkingTimerRef.current = setInterval(() => {
      msgIdx = (msgIdx + 1) % THINKING_MESSAGES.length;
      setSubtitle(THINKING_MESSAGES[msgIdx]);
    }, 2000);

    const controller = new AbortController();
    abortRef.current = controller;

    (async () => {
      // Use Groq for intelligent command routing instead of hardcoding
      const response = await callGroq(input, controller.signal);

      if (thinkingTimerRef.current) {
        clearInterval(thinkingTimerRef.current);
        thinkingTimerRef.current = null;
      }

      if (!response) {
        busyRef.current = false;
        setStatus('LISTENING');
        setSubtitle('Listening…');
        startRecognition();
        return;
      }

      if (response.action === 'clear') {
        setHasData(false);
        setDisplayItems([]);
        moveSphere(false);
        setSubtitle('');
        speak(response.reply || 'Cleared.');
        return;
      }

      let textToSpeak = response.reply;
      let actionItems = response.display || [];

      // Handle Bot Control Actions — call the real API and use the REAL result
      try {
        if (response.action === 'test_email') {
          const apiRes = await fetch(`${API_BASE}/api/test_email`, { method: 'POST' });
          if (apiRes.ok) {
            textToSpeak = response.reply || "Done, Abdullah. Test email sent to your inbox.";
          } else {
            const err = await apiRes.json().catch(() => ({}));
            textToSpeak = `The email failed, Abdullah. Error: ${err.detail || 'Check your Gmail App Password in the .env file.'}`;
          }
        } else if (response.action === 'modify_limits') {
          const apiRes = await fetch(`${API_BASE}/api/modify_limits`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit_type: response.limit_type, new_value: response.new_value })
          });
          if (apiRes.ok) {
            const data = await apiRes.json();
            textToSpeak = response.reply || data.message;
          } else {
            textToSpeak = "I couldn't update the limits. The backend might not be running.";
          }
        } else if (response.action === 'status') {
          const apiRes = await fetch(`${API_BASE}/api/report`);
          if (apiRes.ok) {
            const s = await apiRes.json();
            textToSpeak = response.reply || `The bot is ${s.status}. ${s.posts_today} posts and ${s.replies_today} stealth replies so far today.`;
            actionItems = [
              { type: 'heading', value: 'Bot Status Report' },
              { type: 'stat', value: `Status: ${s.status}` },
              { type: 'stat', value: `Subscribers: ${s.subscribers}` },
              { type: 'stat', value: `Posts Today: ${s.posts_today} / ${s.max_posts}` },
              { type: 'stat', value: `Stealth Replies: ${s.replies_today} / ${s.max_replies}` },
            ];
          } else {
            textToSpeak = "I can't reach the backend server. Make sure main.py is running, Abdullah.";
          }
        } else if (response.action === 'generate_image') {
          const apiRes = await fetch(`${API_BASE}/api/generate_image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ headline: response.headline, category: response.category || 'default' })
          });
          if (apiRes.ok) {
            const data = await apiRes.json();
            textToSpeak = response.reply || "Image generated and saved, Abdullah.";
            if (data.image_url) {
              actionItems = [
                { type: 'heading', value: 'Generated Image' },
                { type: 'image', value: `http://localhost:8000${data.image_url}` }
              ];
            }
          } else {
            textToSpeak = "Image generation failed. The backend might be offline or Pollinations AI timed out.";
          }
        } else if (response.action === 'draft_new_content') {
          textToSpeak = response.reply || "I am dispatching the sub-agent now, Abdullah. I will notify you when the post is ready.";
          actionItems = [
            { type: 'heading', value: 'Sub-Agent Deployed' },
            { type: 'text', value: 'Fetching latest news across all sources...' }
          ];
          
          const cat = encodeURIComponent(response.category || '');
          
          // Fire and forget the stream (Sub-Agent works in background)
          (async () => {
            try {
              const streamRes = await fetch(`${API_BASE}/api/create_post_stream?category=${cat}`);
              if (streamRes.ok && streamRes.body) {
                const reader = streamRes.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let buffer = '';
                
                while (true) {
                  const { done, value } = await reader.read();
                  if (done) break;
                  
                  buffer += decoder.decode(value, { stream: true });
                  const parts = buffer.split('\n\n');
                  buffer = parts.pop();
                  
                  for (const part of parts) {
                    const trimmed = part.trim();
                    if (trimmed.startsWith('data: ')) {
                      try {
                        const eventData = JSON.parse(trimmed.substring(6));
                        
                        if (eventData.step === 'error') {
                          setSubtitle('Sub-agent error: ' + eventData.message);
                          speak('The sub-agent encountered an error.');
                        } else if (eventData.step === 'result') {
                          const pkg = eventData.package;
                          speak("The sub-agent has finished. Here is the generated post, Abdullah.");
                          setSubtitle("Post ready!");
                          
                          const finalItems = [
                            { 
                              type: 'post_preview', 
                              package: pkg,
                              image_url: pkg.image_url ? ('http://localhost:8000' + pkg.image_url) : null
                            }
                          ];
                          
                          setHasData(true);
                          setDisplayItems(finalItems);
                          setPanelLayout('center');
                          moveSphere(true, 'center');
                        } else {
                          // Sub-agent progress report
                          setSubtitle(`Sub-agent: ${eventData.message}`);
                        }
                      } catch (parseErr) {}
                    }
                  }
                }
              }
            } catch (streamErr) {
              console.error("Sub-agent stream error:", streamErr);
              speak('The sub-agent failed to complete the task.');
            }
          })();
          
          // Do not return! Let the main flow render the "Sub-Agent Deployed" message.
        } else if (response.action === 'publish_to_channels') {
          const apiRes = await fetch(`${API_BASE}/api/publish_post`, { method: 'POST' });
          if (apiRes.ok) {
            textToSpeak = response.reply || "The post has been published to your channels, Abdullah!";
            actionItems = [
              { type: 'heading', value: 'Post Published' },
              { type: 'text', value: 'Successfully broadcasted to Telegram and X.' }
            ];
          } else {
            const err = await apiRes.json().catch(() => ({}));
            textToSpeak = `I could not publish the post. ${err.detail || 'Make sure you generated a post first.'}`;
          }
        } else if (response.action === 'stealth_toggle') {
          const apiRes = await fetch(`${API_BASE}/api/stealth/toggle`, { method: 'POST' });
          if (apiRes.ok) {
            const data = await apiRes.json();
            textToSpeak = data.active
              ? "Stealth Marketer has been activated, Abdullah. It is now monitoring competitor groups and running the drip invite strategy. I will notify you via email for every action taken."
              : "Stealth Marketer has been shut down, Abdullah. All scraping and invitation activity has stopped immediately.";
            actionItems = [
              { type: 'heading', value: data.active ? '🟢 STEALTH MARKETER: ACTIVE' : '🔴 STEALTH MARKETER: OFFLINE' },
              { type: 'highlight', value: data.message },
            ];
          } else {
            textToSpeak = "I couldn't toggle the Stealth Marketer. The backend might not be running.";
          }
        } else if (response.action === 'stealth_status') {
          const apiRes = await fetch(`${API_BASE}/api/stealth/status`);
          if (apiRes.ok) {
            const s = await apiRes.json();
            textToSpeak = response.reply || `The Stealth Marketer is currently ${s.active ? 'active' : 'offline'}. ${s.invites_today} invites sent today out of ${s.max_invites_per_day} max.`;
            actionItems = [
              { type: 'heading', value: 'Stealth Marketer Status' },
              { type: 'stat', value: `Status: ${s.active ? '🟢 ACTIVE' : '🔴 OFFLINE'}` },
              { type: 'stat', value: `Reply Mode: ${s.reply_mode ? 'ON' : 'OFF'}` },
              { type: 'stat', value: `Scrape Mode: ${s.scrape_mode ? 'ON' : 'OFF'}` },
              { type: 'stat', value: `Invites Today: ${s.invites_today} / ${s.max_invites_per_day}` },
              { type: 'stat', value: `Emergency Stop: ${s.emergency_stop ? '⚠️ ENGAGED' : '✅ Clear'}` },
              { type: 'stat', value: `Device Fingerprint: ${s.device_fingerprint}` },
              { type: 'stat', value: `Target Groups: ${s.target_groups}` },
              { type: 'stat', value: `Uptime: ${s.uptime_minutes} min` },
            ];
          } else {
            textToSpeak = "I can't reach the Stealth Marketer. Make sure the backend is running.";
          }
        } else if (response.action === 'check_telegram') {
          const apiRes = await fetch(`${API_BASE}/api/telegram/connection_status`);
          if (apiRes.ok) {
            const s = await apiRes.json();
            textToSpeak = s.connected
              ? `Telegram is connected, Abdullah. Logged in as ${s.name}.`
              : "Telegram is NOT connected. You need to authorize it from the dashboard.";
            actionItems = [
              { type: 'heading', value: 'Telegram Connection' },
              { type: 'stat', value: `Status: ${s.connected ? '🟢 Connected' : '🔴 Disconnected'}` },
              { type: 'stat', value: `Name: ${s.name || 'N/A'}` },
              { type: 'stat', value: `Phone: ${s.phone || 'N/A'}` },
            ];
          } else {
            textToSpeak = "I can't check the Telegram connection. Backend might be offline.";
          }
        } else if (response.action === 'check_stealth_connection') {
          const apiRes = await fetch(`${API_BASE}/api/stealth/connection_status`);
          if (apiRes.ok) {
            const s = await apiRes.json();
            textToSpeak = s.connected
              ? `The Stealth Marketer account is connected, Abdullah. Logged in as ${s.name}.`
              : "The Stealth Marketer account is NOT connected. You need to authorize the burner number from the dashboard.";
            actionItems = [
              { type: 'heading', value: 'Stealth Connection' },
              { type: 'stat', value: `Status: ${s.connected ? '🟢 Connected' : '🔴 Disconnected'}` },
              { type: 'stat', value: `Name: ${s.name || 'N/A'}` },
            ];
          } else {
            textToSpeak = "I can't check the Stealth connection. Backend might be offline.";
          }
        }
      } catch (err) {
        console.error("API Action Error:", err);
        textToSpeak = "I tried to execute your command, but the backend server at localhost 8000 is not reachable. Make sure main.py is running.";
      }

      const items = actionItems;
      const layoutChoice = response.layout || 'right';

      // Fallback: if AI forgot "reply" but sent display text, read the text
      if (!textToSpeak && items.length > 0) {
        textToSpeak = items.map(i => i.value).join('. ');
      }

      console.log("AI Response:", response);
      console.log("Speaking text:", textToSpeak);

      if (items.length > 0) {
        setHasData(true);
        setDisplayItems(items);
        setPanelLayout(layoutChoice);
        moveSphere(true, layoutChoice);
        setSubtitle('');
      } else {
        setHasData(false);
        setDisplayItems([]);
        moveSphere(false);
        setSubtitle(textToSpeak || '');
      }

      speak(textToSpeak || 'Done.');
    })();
  }, [stopRecognition, startRecognition, moveSphere, speak]);

  /* ── Boot ───────────────────────────────────────────────── */
  const handleInit = useCallback(() => {
    if (initRef.current) return;
    initRef.current = true;

    try {
      window.speechSynthesis?.getVoices();
      if (window.speechSynthesis?.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
      }
    } catch (_) { }

    setInitialized(true);
    initRecognition();

    setTimeout(() => {
      try { recRef.current?.start(); } catch (_) { }
      speak('Novi is online.');
    }, 600);
  }, [initRecognition, speak]);

  /* ── Cleanup ───────────────────────────────────────────── */
  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
      if (thinkingTimerRef.current) clearInterval(thinkingTimerRef.current);
      try { window.speechSynthesis?.cancel(); } catch (_) { }
      try { recRef.current?.abort(); } catch (_) { }
    };
  }, []);

  const aiState = isSpeaking ? 'speaking'
    : status === 'THINKING' ? 'thinking'
      : isListening ? 'listening'
        : 'idle';

  /* ═══════════════════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════════════════ */
  return (
    <div className="app-container">
      <div className="canvas-container">
        <Canvas
          camera={{ position: [0, 0, 6], fov: 50 }}
          dpr={[1, 2]}
          onCreated={({ gl }) => gl.setClearColor('#000000')}
        >
          <ambientLight intensity={0.08} />
          {initialized && (
            <Suspense fallback={null}>
              <ChatGPTOrb
                aiState={aiState}
                targetX={sphereX}
                targetY={sphereY}
                targetScale={sphereScale}
              />
            </Suspense>
          )}
        </Canvas>
      </div>

      <div className="ui-layer">
        <header className="header">
          <h1 className="logo">
            NOVI
            {initialized && (
              <span className={`status-badge status-${status.toLowerCase()}`}>
                <span className="pulse-dot" />
                {status}
              </span>
            )}
          </h1>

          {/* Control Buttons */}
          {initialized && (
            <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
              {/* Mic Toggle Button */}
              <button
                id="mic-toggle-btn"
                className="control-btn"
                onClick={() => {
                  if (micEnabled) {
                    // Pause mic
                    voicePausedRef.current = true;
                    setMicEnabled(false);
                    stopRecognition();
                    setStatus('PAUSED');
                    setSubtitle('Voice paused. Say "NOVI" to wake me up.');
                  } else {
                    // Resume mic
                    voicePausedRef.current = false;
                    setMicEnabled(true);
                    setStatus('LISTENING');
                    setSubtitle('Listening…');
                    startRecognition();
                  }
                }}
                style={{
                  background: micEnabled ? 'rgba(56, 189, 95, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  border: `1px solid ${micEnabled ? 'rgba(56, 189, 95, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                  color: micEnabled ? '#38bd5f' : '#ef4444',
                  padding: '6px 16px',
                  borderRadius: '20px',
                  fontSize: '0.65rem',
                  fontWeight: 500,
                  letterSpacing: '1.5px',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  textTransform: 'uppercase',
                  transition: 'all 0.3s ease',
                  backdropFilter: 'blur(12px)',
                }}
              >
                {micEnabled ? '🎤 LISTENING' : '🔇 PAUSED'}
              </button>

              {/* Stealth Toggle Button */}
              <button
                id="stealth-toggle-btn"
                className="control-btn"
                onClick={async () => {
                  setSubtitle('Toggling Stealth Marketer...');
                  try {
                    const res = await fetch(`${API_BASE}/api/stealth/toggle`, { method: 'POST' });
                    if (res.ok) {
                      const data = await res.json();
                      const msg = data.active 
                        ? '🟢 Stealth Marketer ACTIVATED.'
                        : '🔴 Stealth Marketer DEACTIVATED.';
                      setSubtitle(msg);
                      speak(data.active 
                        ? 'Stealth Marketer activated, Abdullah.'
                        : 'Stealth Marketer deactivated.');
                      
                      // Also show it in the data panel
                      setHasData(true);
                      setDisplayItems([
                        { type: 'heading', value: data.active ? '🟢 STEALTH: ACTIVE' : '🔴 STEALTH: OFFLINE' },
                        { type: 'highlight', value: msg }
                      ]);
                      setPanelLayout('center');
                      moveSphere(true, 'center');
                    }
                  } catch (err) {
                    setSubtitle('Error: Cannot reach backend server.');
                    speak('Cannot reach the backend server.');
                  }
                }}
                style={{
                  background: 'rgba(99, 102, 241, 0.15)',
                  border: '1px solid rgba(99, 102, 241, 0.4)',
                  color: '#818cf8',
                  padding: '6px 16px',
                  borderRadius: '20px',
                  fontSize: '0.65rem',
                  fontWeight: 500,
                  letterSpacing: '1.5px',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  textTransform: 'uppercase',
                  transition: 'all 0.3s ease',
                  backdropFilter: 'blur(12px)',
                }}
              >
                🕵️ STEALTH
              </button>
            </div>
          )}
        </header>

        {/* Loading UI overlay */}
        <div className={`data-panel-wrapper layout-center ${status === 'THINKING' && !hasData ? 'visible' : ''}`} style={{ zIndex: 10, pointerEvents: 'none' }}>
          {status === 'THINKING' && !hasData && (
            <div className="glass-panel" style={{ alignItems: 'center', justifyContent: 'center', minHeight: '200px', width: '300px', margin: '0 auto', textAlign: 'center' }}>
              <div style={{ width: '40px', height: '40px', border: '3px solid rgba(255,255,255,0.1)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
              <h3 style={{ color: '#fff', letterSpacing: '2px', fontSize: '0.9rem', marginBottom: '8px' }}>PROCESSING</h3>
              <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.75rem', margin: 0 }}>Please wait a moment...</p>
            </div>
          )}
        </div>

        {/* Rich Data Panel */}
        <div className={`data-panel-wrapper ${hasData ? 'visible' : ''} layout-${panelLayout}`}>
          {hasData && (
            <div className="glass-panel">
              {displayItems.map((item, i) => {
                const delay = { animationDelay: `${i * 0.12}s` };

                if (item.type === 'large') {
                  return <div key={i} className="display-large card-anim" style={delay}>{item.value}</div>;
                }
                if (item.type === 'heading') {
                  return <h2 key={i} className="display-heading card-anim" style={delay}>{item.value}</h2>;
                }
                if (item.type === 'stat') {
                  const parts = item.value.split(':');
                  const label = parts[0]?.trim();
                  const val = parts.slice(1).join(':')?.trim();
                  return (
                    <div key={i} className="display-stat card-anim" style={delay}>
                      <span className="stat-dot" />
                      <span className="stat-label">{label}</span>
                      {val && <span className="stat-value">{val}</span>}
                    </div>
                  );
                }
                if (item.type === 'image') {
                  return (
                    <div key={i} className="display-image card-anim" style={delay}>
                      <img src={item.value} alt="Generated UI Output" style={{ maxWidth: '100%', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }} />
                    </div>
                  );
                }
                if (item.type === 'post_preview') {
                  const p = item.package;
                  return (
                    <div key={i} className="post-preview card-anim" style={delay}>
                      {p.real_image_url && (
                        <div className="post-preview-real-img" style={{ padding: '12px 20px 0 20px' }}>
                          <h4 style={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.35)', marginBottom: '6px', letterSpacing: '1px' }}>REAL NEWS PHOTO</h4>
                          <img src={p.real_image_url} alt="Real news" style={{ width: '100%', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }} />
                        </div>
                      )}
                      
                      <div className="post-preview-content">
                        {/* ── Telegram Post ── */}
                        <div className="post-preview-platform">
                          <div className="platform-header">
                            <span className="platform-icon" style={{ background: '#0088cc' }}>T</span>
                            <h4>TELEGRAM POST</h4>
                          </div>
                          {item.image_url && (
                            <div style={{ marginBottom: '24px' }}>
                              <img src={item.image_url} alt="Telegram thumbnail" style={{ width: '100%', borderRadius: '16px', boxShadow: '0 10px 30px rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.05)' }} />
                              {p.headline && (
                                <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#fff', marginTop: '20px', marginBottom: '8px', lineHeight: 1.4, letterSpacing: '0.5px' }}>
                                  {p.headline}
                                </h3>
                              )}
                            </div>
                          )}
                          <p>{p.telegram_text}</p>
                        </div>
                        
                        {/* ── Twitter/X Post ── */}
                        <div className="post-preview-platform">
                          <div className="platform-header">
                            <span className="platform-icon" style={{ background: '#1d9bf0' }}>𝕏</span>
                            <h4>TWEET / X POST</h4>
                          </div>
                          {item.image_url && (
                            <div style={{ marginBottom: '24px' }}>
                              <img src={item.image_url} alt="Twitter thumbnail" style={{ width: '100%', borderRadius: '16px', boxShadow: '0 10px 30px rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.05)' }} />
                              {p.headline && (
                                <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#fff', marginTop: '20px', marginBottom: '8px', lineHeight: 1.4, letterSpacing: '0.5px' }}>
                                  {p.headline}
                                </h3>
                              )}
                            </div>
                          )}
                          <p>{p.tweet_text}</p>
                        </div>
                        
                        {/* ── Reddit Post ── */}
                        {p.reddit_title && (
                          <div className="post-preview-platform">
                            <div className="platform-header">
                              <span className="platform-icon" style={{ background: '#ff4500' }}>R</span>
                              <h4>REDDIT POST</h4>
                            </div>
                            {item.image_url && (
                              <div style={{ marginBottom: '24px' }}>
                                <img src={item.image_url} alt="Reddit thumbnail" style={{ width: '100%', borderRadius: '16px', boxShadow: '0 10px 30px rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.05)' }} />
                              </div>
                            )}
                            <p style={{ fontWeight: 600, marginBottom: '6px', color: 'rgba(255,255,255,0.95)' }}>{p.reddit_title}</p>
                            <p style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.7)' }}>{p.reddit_body}</p>
                          </div>
                        )}
                        
                        <div className="post-preview-meta">
                          <span className="source-credits">Sources: {p.source_credits}</span>
                        </div>
                      </div>
                    </div>
                  );
                }
                if (item.type === 'highlight') {
                  return <div key={i} className="display-highlight card-anim" style={delay}>{item.value}</div>;
                }
                return <div key={i} className="display-text card-anim" style={delay}>{item.value}</div>;
              })}
            </div>
          )}
        </div>

        {initialized && (
          <div className="subtitle-bar">
            <span className={`subtitle ${status === 'THINKING' ? 'thinking-pulse' : ''}`}>
              {subtitle}
            </span>
          </div>
        )}
      </div>

      {!initialized && (
        <button className="init-btn" onClick={handleInit}>
          INITIALIZE
        </button>
      )}
    </div>
  );
}

export default App;
