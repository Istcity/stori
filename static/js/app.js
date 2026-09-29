// StoryTime Studio Client Application Logic
const state = {
  activeProjectId: "demo_story",
  project: null,
  ws: null,
  sfxAudio: new Audio()
};

document.addEventListener("DOMContentLoaded", async () => {
  initWebSocket();
  await checkSystemStatus();
  await loadProject(state.activeProjectId);
  setupEventListeners();
  startSubtitleAnimationDemo();
});

// 1. WebSocket for Real-time Render Telemetry
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/render-progress`;
  
  try {
    state.ws = new WebSocket(wsUrl);
    state.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      appendTerminalLog(data.message, data.step ? "log-info" : "log-line");
    };
    state.ws.onclose = () => {
      setTimeout(initWebSocket, 3000);
    };
  } catch (e) {
    console.warn("WebSocket init error:", e);
  }
}

function appendTerminalLog(msg, cssClass = "log-line") {
  const term = document.getElementById("terminalLogs");
  if (!term) return;
  const timeStr = new Date().toLocaleTimeString();
  const line = document.createElement("div");
  line.className = `log-line ${cssClass}`;
  line.textContent = `[${timeStr}] ${msg}`;
  term.appendChild(line);
  term.scrollTop = term.scrollHeight;
}

// 2. System Status & MCP Health Check
async function checkSystemStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    const comfyDot = document.getElementById("comfyDot");
    const comfyLabel = document.getElementById("comfyLabel");
    if (data.engines.comfyui) {
      comfyDot.className = "status-dot";
      comfyLabel.textContent = "ComfyUI: Connected (8188)";
    } else {
      comfyDot.className = "status-dot comfy-offline";
      comfyLabel.textContent = "ComfyUI: Offline (Procedural Fallback Ready)";
    }

    // Populate voice dropdown
    const voiceSelect = document.getElementById("voiceSelect");
    if (voiceSelect && data.available_voices) {
      voiceSelect.innerHTML = "";
      data.available_voices.forEach(v => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = v.name;
        voiceSelect.appendChild(opt);
      });
    }
  } catch (e) {
    console.error("Status check failed:", e);
  }
}

// 3. Project Management
async function loadProject(projectId) {
  try {
    appendTerminalLog(`Loading project ${projectId}...`, "log-info");
    const res = await fetch(`/api/projects/${projectId}`);
    if (res.ok) {
      state.project = await res.json();
      state.activeProjectId = projectId;
      renderProjectUI();
      appendTerminalLog(`Project '${state.project.project_title}' loaded (${state.project.scenes.length} scenes)`, "log-success");
    } else {
      // Create default
      await createDefaultProject(projectId);
    }
  } catch (e) {
    console.error("Load project error:", e);
  }
}

async function createDefaultProject(projectId) {
  const defaultStory = 
    "O gün hayatımın en büyük rezilliğini yaşayacağımdan tamamen habersizdim. " +
    "Sabah erkenden kalkıp okula doğru yola çıktım. " +
    "Birden pantolonumun arkasının boydan boya yırtık olduğunu fark ettim!";

  const payload = {
    project_id: projectId,
    project_title: "My Most Chaotic Day",
    raw_story_text: defaultStory,
    character_name: "Sinan"
  };

  const res = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  state.project = await res.json();
  renderProjectUI();
}

function renderProjectUI() {
  if (!state.project) return;
  const p = state.project;

  // Form Fields
  document.getElementById("storyTitleInput").value = p.project_title || "";
  document.getElementById("storyTextInput").value = p.raw_story_text || "";
  document.getElementById("charNameInput").value = p.character_profile?.name || "MainProtagonist";

  // Style Selector
  const styleSelect = document.getElementById("styleSelect");
  if (styleSelect && p.character_profile?.style_tag) {
    styleSelect.value = p.character_profile.style_tag;
  }

  // Palette
  const pal = p.character_profile?.palette || {};
  document.getElementById("hairColor").value = pal.hair || "#2D1B18";
  document.getElementById("skinColor").value = pal.skin || "#FFE0BD";
  document.getElementById("hoodieColor").value = pal.hoodie || "#2563EB";
  document.getElementById("lineColor").value = pal.line || "#1E293B";

  // Anchor Image
  updateAnchorPreview();

  // Settings
  document.getElementById("subtitleColor").value = p.render_settings?.highlight_color || "#FFDE59";
  document.getElementById("subtitlesToggle").checked = p.render_settings?.include_subtitles !== false;

  // Scenes Timeline
  renderScenesTimeline();

  // Video Output
  if (p.output_video_path) {
    displayFinalVideo(`/projects_files/${state.activeProjectId}/output/final_storytime.mp4`);
  }
}

function updateAnchorPreview() {
  const img = document.getElementById("anchorImg");
  if (!img) return;
  const rand = Math.random();
  const style = state.project?.character_profile?.style_tag || document.getElementById("styleSelect")?.value;
  
  if (style === "authentic_beach_with_boy" || style === "hybrid_beach_boy") {
    img.src = `/projects_files/${state.activeProjectId}/anchor.png?t=${rand}`;
    img.onerror = () => { img.src = "/assets/stock_animations/thumb_composite_beach_boy.png"; };
  } else if (style === "authentic_beach_family" || style === "vyond_beach_family") {
    img.src = `/projects_files/${state.activeProjectId}/anchor.png?t=${rand}`;
    img.onerror = () => { img.src = "/assets/stock_animations/thumb_beach_family.png"; };
  } else if (style === "authentic_green_screen_boy" || style === "green_screen_modern_boy") {
    img.src = `/projects_files/${state.activeProjectId}/anchor.png?t=${rand}`;
    img.onerror = () => { img.src = "/assets/stock_animations/thumb_boy_green_screen.png"; };
  } else {
    img.src = `/projects_files/${state.activeProjectId}/anchor.png?t=${rand}`;
    img.onerror = () => { img.src = "/assets/characters/anchor.png"; };
  }
}

function renderScenesTimeline() {
  const container = document.getElementById("timelineContainer");
  const countBadge = document.getElementById("sceneCountBadge");
  if (!container) return;

  const scenes = state.project.scenes || [];
  countBadge.textContent = `${scenes.length} Scenes`;

  if (scenes.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 3rem 1rem; color: var(--text-dim);">
        <i class="fa-solid fa-film" style="font-size: 2.5rem; margin-bottom: 0.75rem; opacity: 0.5;"></i>
        <p>Henüz sahne oluşturulmadı.</p>
        <p style="font-size: 0.8rem; margin-top: 0.25rem;">Sol paneldeki "Hikayeyi Sahnelere Böl" butonuna basarak yapay zekanın episodic sahneleri oluşturmasını sağlayın.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = "";
  scenes.forEach((s, idx) => {
    const card = document.createElement("div");
    card.className = "scene-card";
    const thumbSrc = s.assets?.image_plate ? `/${s.assets.image_plate}?t=${Date.now()}` : "/assets/characters/action_scene_test.png";
    
    const typeColors = {
      "physical_action": "background: rgba(14, 165, 233, 0.25); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.4);",
      "slapstick": "background: rgba(244, 63, 94, 0.25); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.4);",
      "environmental_gag": "background: rgba(245, 158, 11, 0.25); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4);",
      "reaction_shot": "background: rgba(168, 85, 247, 0.25); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4);"
    };
    const typeStyle = typeColors[s.scene_type] || "background: rgba(99, 102, 241, 0.2); color: #818cf8;";

    card.innerHTML = `
      <div class="scene-thumb">
        <img src="${thumbSrc}" alt="Scene ${s.scene_id}" onerror="this.src='/assets/characters/action_scene_test.png'">
        <div class="scene-badge-row">
          <span class="badge badge-order">#${s.order}</span>
          <span class="badge badge-duration">${s.duration_sec.toFixed(1)}s</span>
        </div>
      </div>
      <div class="scene-content">
        <div style="display: flex; align-items: center; gap: 0.5rem; justify-content: space-between;">
          <span class="badge" style="${typeStyle}">${(s.scene_type || "ACTION").toUpperCase().replace('_', ' ')}</span>
          <span class="badge badge-status-ready">${s.status}</span>
        </div>
        <div class="scene-narration">${escapeHtml(s.narration_text)}</div>
        <div style="font-size: 0.8rem; color: #38bdf8; background: rgba(15, 23, 42, 0.6); padding: 5px 8px; border-radius: 6px; border-left: 3px solid #0284c7;">
          🏃 <b>Aksiyon:</b> ${escapeHtml(s.character_action || s.visual_prompt || "Fiziksel animasyon hareketi")}
        </div>
        <div class="scene-meta-row">
          <span class="meta-chip">🎥 <b>${s.camera_shot || s.camera_motion}</b></span>
          <span class="meta-chip">🎭 <b>${s.character_emotion}</b></span>
          ${s.sfx_cue ? `<span class="meta-chip chip-sfx" onclick="playSfx('${s.sfx_cue}')" style="cursor: pointer;">🔊 SFX: <b>${s.sfx_cue}</b> ▶</span>` : ""}
          <span class="meta-chip">⚡ Mod: <b>${s.animation_mode}</b></span>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// 4. Action Handlers
function setupEventListeners() {
  // Style Selector Change
  const styleSelect = document.getElementById("styleSelect");
  if (styleSelect) {
    styleSelect.addEventListener("change", async (e) => {
      const selectedStyle = e.target.value;
      if (state.project?.character_profile) {
        state.project.character_profile.style_tag = selectedStyle;
      }
      updateAnchorPreview();
      appendTerminalLog(`Görsel Animasyon Stili Seçildi: ${selectedStyle}`, "log-info");
      
      // Auto-save and regenerate anchor
      await fetch(`/api/projects/${state.activeProjectId}/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.project)
      });
      await fetch(`/api/projects/${state.activeProjectId}/character-sheet`, { method: "POST" });
      updateAnchorPreview();
    });
  }

  // Decompose Button
  document.getElementById("btnDecompose").addEventListener("click", async () => {
    const storyText = document.getElementById("storyTextInput").value.trim();
    if (!storyText) {
      alert("Lütfen önce hikaye metnini girin!");
      return;
    }

    state.project.raw_story_text = storyText;
    state.project.project_title = document.getElementById("storyTitleInput").value.trim();
    state.project.character_profile.name = document.getElementById("charNameInput").value.trim();
    if (styleSelect) {
      state.project.character_profile.style_tag = styleSelect.value;
    }

    appendTerminalLog("Running Scene Decomposition (LLM / Episodic Engine)...", "log-info");
    
    // Save first
    await fetch(`/api/projects/${state.activeProjectId}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.project)
    });

    const res = await fetch(`/api/projects/${state.activeProjectId}/decompose`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pacing: document.getElementById("pacingSelect").value })
    });

    if (res.ok) {
      state.project = await res.json();
      renderScenesTimeline();
      appendTerminalLog(`Successfully sliced into ${state.project.scenes.length} episodic scenes!`, "log-success");
    }
  });

  // Regenerate Character Sheet
  document.getElementById("btnRegenChar").addEventListener("click", async () => {
    appendTerminalLog("Regenerating Character Anchor Model Sheet...", "log-info");
    syncPaletteToState();
    await fetch(`/api/projects/${state.activeProjectId}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.project)
    });

    const res = await fetch(`/api/projects/${state.activeProjectId}/character-sheet`, { method: "POST" });
    if (res.ok) {
      updateAnchorPreview();
      appendTerminalLog("Character Model Sheet updated successfully!", "log-success");
    }
  });

  // Color Pickers auto-sync
  ["hairColor", "skinColor", "hoodieColor", "lineColor"].forEach(id => {
    document.getElementById(id).addEventListener("input", () => {
      syncPaletteToState();
    });
  });

  // Subtitle Color
  document.getElementById("subtitleColor").addEventListener("input", (e) => {
    const color = e.target.value;
    state.project.render_settings.highlight_color = color;
    document.querySelectorAll(".word-highlight").forEach(el => {
      el.style.color = color;
      el.style.textShadow = `0 0 12px ${color}99`;
    });
  });

  // Master Render All Button
  document.getElementById("btnRenderAll").addEventListener("click", async () => {
    const btn = document.getElementById("btnRenderAll");
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Rendering Master Video...`;

    try {
      appendTerminalLog("==========================================", "log-info");
      appendTerminalLog("STARTING FULL END-TO-END MASTER RENDER", "log-info");
      appendTerminalLog("==========================================", "log-info");

      syncPaletteToState();
      await fetch(`/api/projects/${state.activeProjectId}/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.project)
      });

      const voice = document.getElementById("voiceSelect").value;
      const res = await fetch(`/api/projects/${state.activeProjectId}/render-all`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_name: voice })
      });

      const data = await res.json();
      if (data.success) {
        appendTerminalLog(`RENDER COMPLETE! File size: ${(data.file_size / 1024 / 1024).toFixed(2)} MB`, "log-success");
        displayFinalVideo(data.video_url);
        // Refresh project
        await loadProject(state.activeProjectId);
      } else {
        appendTerminalLog("Render encountered an issue.", "log-error");
      }
    } catch (e) {
      appendTerminalLog(`Error: ${e.message}`, "log-error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> One-Click Render Video (1080p)`;
    }
  });

  // BGM Preview Button
  document.getElementById("btnPlayBgm").addEventListener("click", () => {
    playSfx("bgm");
  });
}

function syncPaletteToState() {
  if (!state.project) return;
  state.project.character_profile.palette = {
    hair: document.getElementById("hairColor").value,
    skin: document.getElementById("skinColor").value,
    hoodie: document.getElementById("hoodieColor").value,
    line: document.getElementById("lineColor").value
  };
}

function displayFinalVideo(videoUrl) {
  const container = document.getElementById("theaterScreen");
  container.innerHTML = `
    <video controls autoplay loop style="width: 100%; height: 100%; border-radius: var(--radius-md);">
      <source src="${videoUrl}?t=${Date.now()}" type="video/mp4">
      Tarayıcınız video etiketini desteklemiyor.
    </video>
  `;
  document.getElementById("btnDownloadVideo").style.display = "inline-flex";
  document.getElementById("btnDownloadVideo").onclick = () => {
    const a = document.createElement("a");
    a.href = videoUrl;
    a.download = `${state.project.project_title || "storytime"}.mp4`;
    a.click();
  };
}

function playSfx(sfxName) {
  let url = `/assets/sfx/${sfxName}.wav`;
  if (sfxName === "bgm") {
    url = "/assets/bgm/storytime_acoustic_loop.wav";
  }
  state.sfxAudio.src = url;
  state.sfxAudio.volume = 0.8;
  state.sfxAudio.play().catch(e => console.log("Audio play allowed after click:", e));
}

// 5. Kinetic Subtitle Live Preview Box Animation
function startSubtitleAnimationDemo() {
  const words = ["HAYATIMIN", "EN", "BÜYÜK", "REZİLLİĞİYDİ!"];
  let activeIdx = 0;
  const container = document.getElementById("kineticDemoLine");
  if (!container) return;

  setInterval(() => {
    const color = document.getElementById("subtitleColor")?.value || "#FFDE59";
    container.innerHTML = words.map((w, idx) => {
      if (idx === activeIdx) {
        return `<span class="word-highlight" style="color: ${color}; text-shadow: 0 0 14px ${color}99;">${w}</span>`;
      }
      return `<span>${w}</span>`;
    }).join(" ");

    activeIdx = (activeIdx + 1) % words.length;
  }, 500);
}
