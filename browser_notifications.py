from __future__ import annotations
import html
import streamlit.components.v1 as components

def render_notification_control(enabled: bool = False):
    label = "Notifications activées" if enabled else "Activer les notifications"
    components.html(f"""
    <div style="font-family:Arial,sans-serif;padding:6px 0">
      <button id="rz-btn" style="padding:10px 14px;border-radius:10px;border:1px solid #888;background:#fff;cursor:pointer;font-weight:700">🔔 {html.escape(label)}</button>
      <div id="rz-status" style="margin-top:6px;font-size:13px;opacity:.75"></div>
    </div>
    <script>
    const btn=document.getElementById('rz-btn'), status=document.getElementById('rz-status');
    function showStatus(){{
      if(!('Notification' in window)){{status.textContent='Ce navigateur ne prend pas en charge les notifications.';return;}}
      status.textContent='État : '+Notification.permission;
    }}
    btn.onclick=async()=>{{
      if(!('Notification' in window)){{showStatus();return;}}
      try{{ const p=await Notification.requestPermission(); showStatus(); if(p==='granted'){{new Notification('RE-ZERO',{{body:'Notifications activées.',tag:'re-zero-enabled'}});}} }}catch(e){{status.textContent='Permission impossible.';}}
    }};
    showStatus();
    </script>
    """, height=100)

def notify_opportunity(alert: dict, key: str):
    if not alert.get('active'): return
    s=alert.get('setup',{}) or {}
    title=f"RE-ZERO • {alert.get('instrument','')} {alert.get('direction','')}"
    body=(f"Qualité {alert.get('grade','')} {float(alert.get('quality',0)):.0f}/100 | "
          f"Entry {s.get('entry','—')} | SL {s.get('sl','—')} | TP1 {s.get('tp1','—')} | TP2 {s.get('tp2','—')} | R:R {s.get('rr','—')}")
    components.html(f"""
    <script>
    try{{
      const key={key!r};
      if('Notification' in window && Notification.permission==='granted' && localStorage.getItem('re_zero_last_alert')!==key){{
        new Notification({title!r},{{body:{body!r},tag:'re-zero-opportunity',renotify:true}});
        localStorage.setItem('re_zero_last_alert',key);
      }}
    }}catch(e){{}}
    </script>
    """, height=1)
