const $=s=>document.querySelector(s),app=$("#app");
const INTERESTS=["AI Agents","AI Models","AI Tools","AI Products","Coding","Productivity","Image Generation","Video Generation","Data Science","Education","Business","Research"];
const PROFS=["Student","Software Developer","Data Scientist / ML Engineer","Researcher","Designer","Product Manager","Founder / Business","Educator","Other"];
let token=localStorage.t,me=null;

const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
// Only allow http(s) links so data can never inject javascript: URLs
const safeUrl=u=>/^https?:\/\//i.test(u||"")?esc(u):"#";

async function api(p,m="GET",b){
  const headers={"Content-Type":"application/json"};
  if(token)headers.Authorization="Bearer "+token;
  const r=await fetch("/api/"+p,{method:m,headers,body:b?JSON.stringify(b):undefined});
  const d=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(typeof d.detail=="string"?d.detail:"Check your input");
  return d;
}

function landing(){
  app.innerHTML = `<section class="hero">
    <div>
      <span class="tag">REAL-TIME AI DISCOVERY</span>
      <h1>Knots</h1>
      <h2>Discover what's new. Connect what's next.</h2>
      <p>Explore emerging AI tools, discover the latest innovations, and stay ahead of what's next in AI.</p>
      <p>
        <button class="btn" onclick="auth('signup')">Sign up</button>
        <button class="btn ghost" onclick="auth('login')">Log in</button>
        <button class="btn ghost" onclick="guest()">Explore releases</button>
      </p>
      <p>
        <span class="tag">12 trusted sources</span>
        <span class="tag">~10–15 min target, not guaranteed</span>
      </p>
    </div>
    <div class="radar"></div>
  </section>`;
}

function auth(mode){
  const su=mode=="signup";
  app.innerHTML=`<div class="auth card"><h2>${su?"Create your account":"Welcome back"}</h2>
 ${su?`<input id=n placeholder="Full name"><select id=pf style="width:100%;padding:11px;margin:6px 0;background:#0b1128;border:1px solid var(--line);border-radius:10px;color:var(--tx)"><option value="">Your profession</option>${PROFS.map(p=>`<option>${esc(p)}</option>`).join("")}</select>`:""}
 <input id=e type=email placeholder="Email"><input id=p type=password placeholder="Password${su?" (8+ characters)":""}">${su?'<input id=c type=password placeholder="Confirm password">':""}
 <p id=err style="color:#ff7a8a"></p><button class=btn id=go>${su?"Sign up":"Log in"}</button>
 <p>${su?'Already signed up? <a href="#" id=sw>Log in</a>':'New here? <a href="#" id=sw>Sign up</a>'} · <a href="#" id=bk>Back</a></p></div>`;
  $("#sw").onclick=e=>{e.preventDefault();auth(su?"login":"signup")};
  $("#bk").onclick=e=>{e.preventDefault();landing()};
  $("#go").onclick=async()=>{
    const err=$("#err");err.textContent="";
    try{
      let body;
      if(su){
        body={name:$("#n").value.trim(),profession:$("#pf").value,email:$("#e").value.trim(),password:$("#p").value,confirm_password:$("#c").value};
        if(!body.name||!body.profession)throw new Error("Enter your name and choose a profession");
        if(body.password.length<8)throw new Error("Password must be at least 8 characters");
        if(body.password!==body.confirm_password)throw new Error("Passwords do not match");
      }else body={email:$("#e").value.trim(),password:$("#p").value};
      const d=await api(mode,"POST",body);
      token=localStorage.t=d.token;
      boot(su);
    }catch(x){err.textContent=x.message}
  };
}

function interestPicker(sel){
  sel=sel||[];
  return INTERESTS.map(i=>`<span class="chip ${sel.includes(i)?"on":""}" data-i="${esc(i)}">${esc(i)}</span>`).join("");
}
function bindChips(){document.querySelectorAll(".chip").forEach(c=>c.onclick=()=>c.classList.toggle("on"))}
const picked=()=>[...document.querySelectorAll(".chip.on")].map(c=>c.dataset.i);

function interests(first){
  $("#main").innerHTML=`<h2>What should your radar watch?</h2><p>Pick what you care about. You'll only get emails for these.</p>${interestPicker(me.interests)}<p><button class=btn id=sv>Save interests</button> <span id=msg class=ok></span></p>`;
  bindChips();
  $("#sv").onclick=async()=>{
    try{
      await api("preferences","PUT",{interests:picked()});
      me.interests=picked();
      $("#msg").textContent="Saved";
      if(first)nav("dashboard");
    }catch(x){$("#msg").textContent=x.message}
  };
}

function relCard(r){
  return `<div class=card><span class=tag>${esc(r.company)}</span><span class=tag>${esc(r.category||"Pending")}</span><span class="tag ok">${r.verification_status=="VERIFIED"?"✓ Verified":esc(r.verification_status)}</span><span class=tag>${esc(r.discovery_source)}</span>
<h3>${esc(r.tool_name)}</h3><p>${esc(r.summary||"Summary pending…")}</p><a href="${safeUrl(r.official_url)}" target=_blank rel=noopener>Official release</a> · <a href="#" onclick="detail(${Number(r.id)});return false">Details &amp; feedback</a></div>`;
}

async function detail(id){
  const r=await api("releases/"+id);
  let d={};
  try{d=typeof r.details=="string"?JSON.parse(r.details||"{}"):(r.details||{})}catch{d={}}
  const L=a=>(a||[]).map(x=>`<li>${esc(x)}</li>`).join("");
  $("#main").innerHTML=`<h2>${esc(r.tool_name)}</h2><p>${esc(r.company)} · ${esc(r.category)} · ${esc(r.verification_status)} · via ${esc(r.discovery_source)}</p>
<div class=card><h4>What is it?</h4>${esc(d.what_it_does||r.summary)}<h4>Key features</h4><ul>${L(d.key_features)}</ul><h4>Useful for</h4>${esc(d.useful_for)}<h4>Use cases</h4><ul>${L(d.use_cases)}</ul><h4>Why it matters</h4>${esc(d.why_it_matters)}</div>
<p>Detected ${esc(r.detected_at)} · Verified ${esc(r.verified_at||"-")} · Notified ${esc(r.notified_at||"-")}</p><a href="${safeUrl(r.official_url)}" target=_blank rel=noopener>Official source</a>
<div class=card><h4>Rate this release (optional)</h4><input id=rt type=number min=1 max=5 placeholder="1–5 stars"><textarea id=rv placeholder="Review"></textarea><button class=btn id=fb>Send feedback</button> <span id=m class=ok></span></div>`;
  $("#fb").onclick=async()=>{
    if(!token){$("#m").textContent="Log in to leave feedback";return}
    const rating=parseInt($("#rt").value,10);
    if(!(rating>=1&&rating<=5)){$("#m").textContent="Enter a rating from 1 to 5";return}
    try{
      await api(`releases/${id}/feedback`,"POST",{rating,review_text:$("#rv").value});
      $("#m").textContent="Thanks!";
    }catch(x){$("#m").textContent=x.message}
  };
}

const views={
  async dashboard(){
    const s=await api("stats"),r=await api("releases"),h=new Date().getHours();
    $("#main").innerHTML=`<h2>Good ${h<12?"morning":h<18?"afternoon":"evening"}, ${esc(me.name)}</h2><p class=ok>● RADAR ACTIVE</p><div class=grid>
 ${[["Sources monitored",s.sources],["Releases detected",s.detected],["Verified",s.verified],["Notifications sent",s.notifications],["Avg alert time",s.avg_alert_minutes==null?"–":s.avg_alert_minutes+" min"]].map(x=>`<div class="card stat"><b>${esc(x[1])}</b>${esc(x[0])}</div>`).join("")}</div>
 <h3>Latest releases</h3>${r.slice(0,6).map(relCard).join("")||"<p>No releases yet. The first check runs within a few minutes of startup.</p>"}`;
  },
  async releases(){
    $("#main").innerHTML="<h2>Latest releases</h2>"+(await api("releases")).map(relCard).join("");
  },
  async sources(){
    $("#main").innerHTML="<h2>Sources</h2>"+(await api("sources")).map(s=>`<div class=card><b>${esc(s.company)}</b> <span class=tag>Tier ${esc(s.tier)}</span><span class=tag>${s.status=="MONITORING"?"● MONITORING":s.status=="NO_FEED_CONFIGURED"?"No feed configured":"⚠️ TEMPORARILY UNAVAILABLE"}</span>
 <p>${esc(s.official_domain)} · last checked ${esc(s.last_checked||"never")}</p><a href="${safeUrl(s.release_page)}" target=_blank rel=noopener>Release page</a></div>`).join("");
  },
  async notifications(){
    const n=await api("notifications");
    $("#main").innerHTML="<h2>Notifications</h2>"+(n.map(x=>`<div class=card><b>${esc(x.tool_name)}</b> <span class=tag>${esc(x.company)}</span><p>${esc(x.sent_at)} · ✓ ${esc(x.status)} · ✓ Relevant · ✓ Verified</p></div>`).join("")||"<p>Nothing sent yet. Pick interests to start receiving matches.</p>");
  },
  feedback(){
    $("#main").innerHTML="<h2>Feedback</h2><p>Open any release and use “Details &amp; feedback” to rate it.</p>";
  },
  async profile(){
    $("#main").innerHTML=`<h2>Profile</h2><div class=card>${esc(me.name)}<br>${esc(me.profession||"")}<br>${esc(me.email)}<br>Joined ${esc(me.created_at)}</div><h3>Interests</h3>${interestPicker(me.interests)}<p><button class=btn id=sv>Update interests</button></p>`;
    bindChips();
    $("#sv").onclick=async()=>{
      try{
        await api("preferences","PUT",{interests:picked()});
        me.interests=picked();
        $("#sv").textContent="Saved";
      }catch(x){$("#sv").textContent=x.message}
    };
  },
  interests(){interests(false)},
  settings(){
    $("#main").innerHTML="<h2>Settings</h2><p>API keys and polling are configured in the server <code>.env</code> file.</p>";
  }
};

async function nav(v){
  document.querySelectorAll(".side a").forEach(a=>a.classList.toggle("on",a.dataset.v==v));
  try{await views[v]()}catch(e){$("#main").innerHTML="<p>"+esc(e.message)+"</p>"}
}

function shell(links,extra){
  app.innerHTML=`<div class=shell><nav class=side><b>AI Release Radar</b>${links.map(v=>`<a data-v=${v}>${v[0].toUpperCase()+v.slice(1)}</a>`).join("")}${extra}</nav><main id=main></main></div>`;
  document.querySelectorAll(".side a[data-v]").forEach(a=>a.onclick=()=>nav(a.dataset.v));
}

function guest(){
  me={name:"there",profession:"",interests:[]};
  shell(["dashboard","releases","sources"],'<a id=si>Sign up</a><a id=li>Log in</a><a id=bk>Back</a>');
  $("#si").onclick=()=>auth("signup");
  $("#li").onclick=()=>auth("login");
  $("#bk").onclick=landing;
  nav("dashboard");
}

async function boot(first){
  if(!token)return landing();
  try{me=await api("me")}catch{localStorage.removeItem("t");token=null;return landing()}
  me.interests=me.interests||[];
  shell(["dashboard","releases","sources","interests","notifications","feedback","profile","settings"],'<a id=out>Logout</a>');
  $("#out").onclick=()=>{localStorage.removeItem("t");token=null;landing()};
  first?interests(true):nav("dashboard");
}
boot();