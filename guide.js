/*
 * MathGuide —— 数学天赋星图新手指引引擎（零依赖，原生 JS+CSS）
 * 提供：图文欢迎弹层 + 分步高亮 tour（聚光罩 + 气泡）+ 右下「?」重看按钮 + localStorage 记忆。
 * 用法：
 *   MathGuide.run({ page:'index', welcome:{title,subtitle,points,cta}, steps:[...] })
 *   MathGuide.openTour() / MathGuide.openWelcome()
 * 每步：{ target:'#sel-domain'|null, title, body, placement:'top|bottom|left|right', onEnter?(), onLeave?() }
 */
(function () {
  "use strict";

  var LS_WELCOME = "mathtree.guide.welcome.v1";
  var LS_TOUR = "mathtree.guide.tour.v1:";

  // ---------- 样式注入 ----------
  var css = [
    ".mg-overlay{position:fixed;inset:0;z-index:9000;background:rgba(4,7,17,.72);",
    "  backdrop-filter:blur(2px);display:flex;align-items:center;justify-content:center;",
    "  opacity:0;transition:opacity .25s ease;}",
    ".mg-overlay.mg-show{opacity:1;}",
    ".mg-modal{max-width:460px;width:calc(100% - 40px);background:rgba(16,21,40,.92);",
    "  border:1px solid var(--gold,#ffcf4d);border-radius:18px;padding:28px 30px;",
    "  box-shadow:0 0 60px rgba(255,207,77,.18);color:#e9edff;font-family:inherit;",
    "  transform:translateY(12px) scale(.98);transition:transform .25s ease;}",
    ".mg-overlay.mg-show .mg-modal{transform:translateY(0) scale(1);}",
    ".mg-modal h2{margin:0 0 6px;color:var(--gold,#ffcf4d);font-size:22px;letter-spacing:.5px;}",
    ".mg-modal .mg-sub{margin:0 0 16px;color:#8b95b8;font-size:13px;line-height:1.6;}",
    ".mg-modal ul{margin:0 0 20px;padding-left:0;list-style:none;}",
    ".mg-modal li{font-size:14px;line-height:1.9;color:#e9edff;}",
    ".mg-modal li b{color:#7cc4ff;}",
    ".mg-modal .mg-actions{display:flex;gap:12px;justify-content:flex-end;}",
    ".mg-btn{cursor:pointer;border-radius:10px;padding:9px 18px;font-size:13px;font-weight:600;",
    "  border:1px solid rgba(255,255,255,.18);background:transparent;color:#cdd4ee;",
    "  transition:all .18s ease;font-family:inherit;}",
    ".mg-btn:hover{border-color:#7cc4ff;color:#fff;}",
    ".mg-btn.mg-primary{background:linear-gradient(180deg,#ffd96b,#f3b73c);border-color:#ffcf4d;",
    "  color:#241a00;box-shadow:0 0 22px rgba(255,207,77,.28);}",
    ".mg-btn.mg-primary:hover{filter:brightness(1.06);color:#241a00;}",

    ".mg-tour-mask{position:fixed;inset:0;z-index:9001;pointer-events:none;}",
    ".mg-spot{position:absolute;border-radius:14px;box-shadow:0 0 0 9999px rgba(4,7,17,.72);",
    "  transition:all .3s cubic-bezier(.4,0,.2,1);pointer-events:none;}",
    ".mg-spot.mg-rect{border-radius:6px;}",
    ".mg-pop{position:fixed;z-index:9002;max-width:320px;width:calc(100% - 36px);",
    "  background:rgba(16,21,40,.96);border:1px solid #7cc4ff;border-radius:14px;padding:16px 18px;",
    "  box-shadow:0 0 40px rgba(124,196,255,.2);color:#e9edff;font-family:inherit;",
    "  transform:translateY(8px);opacity:0;transition:opacity .2s ease,transform .2s ease;}",
    ".mg-pop.mg-show{opacity:1;transform:translateY(0);}",
    ".mg-pop h4{margin:0 0 8px;color:#7cc4ff;font-size:15px;}",
    ".mg-pop p{margin:0 0 14px;font-size:13.5px;line-height:1.65;color:#e9edff;}",
    ".mg-pop .mg-foot{display:flex;align-items:center;justify-content:space-between;}",
    ".mg-pop .mg-step{font-size:12px;color:#8b95b8;}",
    ".mg-pop .mg-nav{display:flex;gap:8px;}",

    ".mg-fab{position:fixed;right:20px;bottom:20px;z-index:8999;width:46px;height:46px;",
    "  border-radius:50%;border:1.5px solid var(--gold,#ffcf4d);background:rgba(16,21,40,.9);",
    "  color:var(--gold,#ffcf4d);font-size:22px;font-weight:700;cursor:pointer;",
    "  display:flex;align-items:center;justify-content:center;font-family:inherit;",
    "  box-shadow:0 0 24px rgba(255,207,77,.25);transition:transform .18s ease,box-shadow .18s ease;}",
    ".mg-fab:hover{transform:scale(1.08);box-shadow:0 0 32px rgba(255,207,77,.4);}",

    "@media (prefers-reduced-motion: reduce){",
    "  .mg-overlay,.mg-modal,.mg-spot,.mg-pop,.mg-fab{transition:none!important;animation:none!important;}}",

    "@media (max-width:560px){",
    "  .mg-pop{left:50%!important;top:auto!important;bottom:76px!important;transform:translateX(-50%) translateY(8px);}",
    "  .mg-pop.mg-show{transform:translateX(-50%) translateY(0);}}"
  ].join("\n");

  function injectStyle() {
    if (document.getElementById("mg-style")) return;
    var s = document.createElement("style");
    s.id = "mg-style";
    s.textContent = css;
    document.head.appendChild(s);
  }

  // ---------- 工具 ----------
  function $(sel) { return document.querySelector(sel); }
  function ce(tag, cls) { var e = document.createElement(tag); if (cls) e.className = cls; return e; }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function targetEl(step) {
    if (!step || !step.target) return null;
    try { return typeof step.target === "function" ? step.target() : document.querySelector(step.target); }
    catch (e) { return null; }
  }
  function rectOf(step) {
    var el = targetEl(step);
    if (!el || !el.getBoundingClientRect) return null;
    var r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return null;
    return r;
  }

  // 侧栏（左侧 HUD）相关：讲解侧栏内容时展开它，并把目标滚动到可视区中央，
  // 以避开移动端顶部横条 HUD 对侧栏顶部的遮挡。
  function isInSidebar(step) {
    var el = targetEl(step);
    return !!(el && el.closest && el.closest("#sidebar"));
  }
  function setSidebar(open) {
    if (!document.body) return;
    if (open) document.body.classList.remove("sidebar-collapsed");
    else document.body.classList.add("sidebar-collapsed");
  }

  // ---------- 欢迎弹层 ----------
  function welcomeSeen() { return lsGet(LS_WELCOME) === "1"; }
  function markWelcome() { lsSet(LS_WELCOME, "1"); }

  function openWelcome(cfg, onDone) {
    injectStyle();
    var ov = ce("div", "mg-overlay");
    var modal = ce("div", "mg-modal");
    var h = ce("h2"); h.textContent = cfg.title || "欢迎来到数学天赋星图";
    var sub = ce("p", "mg-sub"); sub.textContent = cfg.subtitle || "";
    var ul = ce("ul");
    (cfg.points || []).forEach(function (p) {
      var li = ce("li"); li.innerHTML = p; ul.appendChild(li);
    });
    var actions = ce("div", "mg-actions");
    var skip = ce("button", "mg-btn"); skip.textContent = "跳过";
    var go = ce("button", "mg-btn mg-primary"); go.textContent = cfg.cta || "开始探索";
    actions.appendChild(skip); actions.appendChild(go);
    modal.appendChild(h); modal.appendChild(sub); modal.appendChild(ul); modal.appendChild(actions);
    ov.appendChild(modal);
    document.body.appendChild(ov);
    requestAnimationFrame(function () { ov.classList.add("mg-show"); });
    function close(runTour) {
      ov.classList.remove("mg-show");
      setTimeout(function () {
        if (ov.parentNode) ov.parentNode.removeChild(ov);
        if (runTour && onDone) onDone();
      }, 240);
    }
    skip.onclick = function () { close(false); };
    go.onclick = function () { close(true); };
  }

  // ---------- Tour ----------
  function tourSeen(page) { return lsGet(LS_TOUR + page) === "1"; }
  function markTour(page) { lsSet(LS_TOUR + page, "1"); }

  var tourState = null;

  function openTour(page, steps, startIdx) {
    injectStyle();
    if (tourState) return; // 已在运行
    if (!steps || !steps.length) return;
    var mask = ce("div", "mg-tour-mask");
    var spot = ce("div", "mg-spot");
    var pop = ce("div", "mg-pop");
    document.body.appendChild(mask);
    document.body.appendChild(spot);
    document.body.appendChild(pop);

    var idx = startIdx || 0;
    var curStep = null;

    function position() {
      var step = steps[idx];
      var r = rectOf(step);
      var pad = 8;
      if (r) {
        var isRect = step.rect !== false;
        spot.className = "mg-spot" + (isRect ? " mg-rect" : "");
        spot.style.left = (r.left - pad) + "px";
        spot.style.top = (r.top - pad) + "px";
        spot.style.width = (r.width + pad * 2) + "px";
        spot.style.height = (r.height + pad * 2) + "px";
        spot.style.display = "block";
      } else {
        spot.style.display = "none";
      }
      pop.style.visibility = "hidden";
      pop.classList.add("mg-show");
      var pr = pop.getBoundingClientRect();
      var vw = window.innerWidth, vh = window.innerHeight;
      var px, py;
      if (!r) {
        px = (vw - pr.width) / 2;
        py = (vh - pr.height) / 2;
      } else {
        var place = step.placement || "bottom";
        if (place === "top") { px = r.left; py = r.top - pr.height - 14; }
        else if (place === "left") { px = r.left - pr.width - 14; py = r.top + r.height / 2 - pr.height / 2; }
        else if (place === "right") { px = r.right + 14; py = r.top + r.height / 2 - pr.height / 2; }
        else { px = r.left; py = r.bottom + 14; } // bottom
        if (px < 10) px = 10;
        if (px + pr.width > vw - 10) px = vw - pr.width - 10;
        if (py < 10) py = 10;
        if (py + pr.height > vh - 10) py = vh - pr.height - 10;
      }
      pop.style.left = px + "px";
      pop.style.top = py + "px";
      pop.style.visibility = "visible";
    }

    // 定位调度：侧栏步骤需等滑入过渡结束再定位，并把目标滚动到可视区中央
    function schedulePosition(needSidebar) {
      if (needSidebar) {
        spot.style.display = "none";
        pop.style.visibility = "hidden";
        setTimeout(function () {
          var el = targetEl(steps[idx]);
          if (el && el.scrollIntoView) {
            try { el.scrollIntoView({ block: "center", inline: "nearest" }); }
            catch (e) { try { el.scrollIntoView(); } catch (e2) {} }
          }
          position();
        }, 400);
      } else {
        requestAnimationFrame(position);
      }
    }

    function render() {
      var step = steps[idx];
      if (curStep && curStep.onLeave) { try { curStep.onLeave(); } catch (e) {} }
      curStep = step;
      pop.innerHTML = "";
      var h = ce("h4"); h.textContent = step.title || "";
      var p = ce("p"); p.innerHTML = step.body || "";
      var foot = ce("div", "mg-foot");
      var stepTxt = ce("span", "mg-step"); stepTxt.textContent = (idx + 1) + " / " + steps.length;
      var nav = ce("div", "mg-nav");
      var skipBtn = ce("button", "mg-btn"); skipBtn.textContent = "跳过";
      var prevBtn = ce("button", "mg-btn"); prevBtn.textContent = "上一步";
      var nextBtn = ce("button", "mg-btn mg-primary");
      nextBtn.textContent = idx === steps.length - 1 ? "完成" : "下一步";
      nav.appendChild(skipBtn);
      if (idx > 0) nav.appendChild(prevBtn);
      nav.appendChild(nextBtn);
      foot.appendChild(stepTxt); foot.appendChild(nav);
      pop.appendChild(h); pop.appendChild(p); pop.appendChild(foot);

      if (step.onEnter) { try { step.onEnter(); } catch (e) {} }

      // 侧栏步骤：展开左侧 HUD（若已折叠），并把目标滚动到可视区中央，
      // 同时避开移动端顶部横条 HUD 对侧栏顶部的遮挡；非侧栏步骤则收起侧栏。
      var needSidebar = !!(step.expandSidebar || isInSidebar(step));
      setSidebar(needSidebar);
      schedulePosition(needSidebar);

      skipBtn.onclick = finish;
      prevBtn.onclick = function () { if (idx > 0) { idx--; render(); } };
      nextBtn.onclick = function () {
        if (idx < steps.length - 1) { idx++; render(); }
        else finish();
      };
    }

    function finish() {
      if (curStep && curStep.onLeave) { try { curStep.onLeave(); } catch (e) {} }
      markTour(page);
      if (mask.parentNode) mask.parentNode.removeChild(mask);
      if (spot.parentNode) spot.parentNode.removeChild(spot);
      if (pop.parentNode) pop.parentNode.removeChild(pop);
      tourState = null;
      window.removeEventListener("resize", position);
      window.removeEventListener("scroll", position, true);
    }

    tourState = { page: page };
    window.addEventListener("resize", position);
    window.addEventListener("scroll", position, true);
    render();
  }

  // ---------- 「?」悬浮按钮 ----------
  function ensureFab(opts) {
    if (document.getElementById("mg-fab")) return;
    var fab = ce("button", "mg-fab");
    fab.id = "mg-fab";
    fab.title = "新手指引";
    fab.textContent = "?";
    fab.onclick = function () {
      if (window.MathGuide) window.MathGuide.openTour(opts);
    };
    document.body.appendChild(fab);
  }

  // ---------- 公开 API ----------
  function run(cfg) {
    injectStyle();
    var page = cfg.page || "index";
    ensureFab(cfg);
    if (!welcomeSeen()) {
      markWelcome();
      var playTour = !tourSeen(page);
      openWelcome(cfg.welcome || {}, function () {
        if (playTour) openTour(page, cfg.steps || []);
      });
    } else if (!tourSeen(page)) {
      openTour(page, cfg.steps || []);
    }
  }

  function openTourApi(cfg) {
    var page = (cfg && cfg.page) || (tourState && tourState.page) || "index";
    openTour(page, (cfg && cfg.steps) || (window.__mgSteps || []));
  }
  function openWelcomeApi(cfg) {
    openWelcome((cfg && cfg.welcome) || (window.__mgWelcome || {}));
  }

  window.MathGuide = {
    run: run,
    openTour: openTourApi,
    openWelcome: openWelcomeApi
  };
})();
