"""Samurai look for the dashboard: black and crimson styles, a cursor-reactive background, a splash
screen, and the orb loader shown while an agent works.

Everything here is decoration. Nothing in it reads or changes what the agent or the firewall decides.
All motion is switched off when the viewer's system asks for reduced motion.
"""
from __future__ import annotations

import base64
import html

import streamlit as st

FONTS = ("https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@600;800"
         "&family=Yuji+Syuku&family=JetBrains+Mono:wght@400;600&display=swap")

CSS = r"""
@import url('__FONTS__');
:root{
  --sm-ink:#09090b; --sm-line:rgba(255,255,255,.08); --sm-panel:rgba(20,17,22,.78);
  --sm-red:#e0242f; --sm-hot:#ff4545; --sm-deep:#7a0b12; --sm-paper:#f3ece2; --sm-muted:#aba39b; --sm-gold:#c9a45c;
  --sm-green:#43c97f; --sm-amber:#f0b429; --sm-violet:#b07cff; --sm-blue:#5a9bff;
  --sm-serif:'Shippori Mincho B1','Hiragino Mincho ProN','Yu Mincho',Georgia,serif;
  --sm-brush:'Yuji Syuku','Hiragino Mincho ProN','Yu Mincho',serif;
  --sm-mono:'JetBrains Mono',ui-monospace,Menlo,monospace;
  --mx:50vw; --my:30vh; --px:0; --py:0;
}
html,body{background:
  radial-gradient(1100px 650px at 88% -12%, rgba(224,36,47,.16), transparent 60%),
  radial-gradient(900px 600px at -12% 112%, rgba(122,11,18,.30), transparent 60%), var(--sm-ink) fixed;}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stHeader"],[data-testid="stBottomBlockContainer"]{background:transparent !important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(26,8,11,.88),rgba(10,9,12,.9)) !important;
  border-right:1px solid rgba(224,36,47,.22); box-shadow:12px 0 50px -30px rgba(224,36,47,.5); backdrop-filter:blur(6px);}
::selection{background:rgba(224,36,47,.55); color:#fff;}
/* the style and script holders take no room */
[data-testid="stElementContainer"]:has(> .stHtml > script:only-child),
[data-testid="stElementContainer"]:has(style:only-child){display:none;}

/* ---------- type ---------- */
.sm-hero [data-testid="stHeaderActionElements"],.sm-brand [data-testid="stHeaderActionElements"],.sm-colhead [data-testid="stHeaderActionElements"]{display:none !important;}
h1,h2,h3,h4,[data-testid="stHeading"] *{font-family:var(--sm-serif) !important; letter-spacing:.02em;}
.sr-only{position:absolute !important; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0;}

/* ---------- focus stays obvious ---------- */
button:focus-visible,[role="tab"]:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible,[tabindex]:focus-visible{
  outline:2px solid var(--sm-gold) !important; outline-offset:2px !important;}

/* ---------- side nav (a radio group, so arrows and Tab still work) ---------- */
.sm-side-label{display:flex; align-items:center; gap:8px; margin:14px 0 6px; font-size:11px; letter-spacing:.28em; text-transform:uppercase; color:var(--sm-muted);}
.sm-side-label .kj{font-family:var(--sm-brush); font-size:16px; letter-spacing:0; color:var(--sm-red); text-shadow:0 0 12px rgba(224,36,47,.6);}
.sm-side-label::after{content:""; flex:1; height:1px; background:linear-gradient(90deg,rgba(224,36,47,.55),transparent);}
[data-testid="stSidebar"] [data-testid="stRadioGroup"]{gap:4px !important; width:100%;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div{position:relative; overflow:hidden; width:100%; padding:9px 12px 9px 16px; border-radius:10px; border:1px solid transparent;
  transition:background .25s, border-color .25s, transform .2s, box-shadow .25s;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div::before{content:""; position:absolute; left:0; top:16%; bottom:16%; width:3px; border-radius:3px; background:var(--sm-hot);
  box-shadow:0 0 12px var(--sm-hot); transform:scaleY(0); transition:transform .3s cubic-bezier(.2,.9,.25,1);}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div::after{content:""; position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(110deg,transparent 35%,rgba(255,80,80,.22) 50%,transparent 65%); transform:translateX(-110%); transition:transform .6s ease;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] [data-testid="stRadioOption"]{position:static; width:100%; cursor:pointer;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] [data-testid="stRadioOption"]::after{content:""; position:absolute; inset:0; z-index:1;} /* the whole card is clickable */
[data-testid="stSidebar"] [data-testid="stRadioGroup"] [data-testid="stRadioOption"] > div > div:first-child{display:none;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] [data-testid="stRadioOption"] > div{background:transparent !important; box-shadow:none !important; outline:none !important;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:hover{background:rgba(224,36,47,.08); border-color:rgba(224,36,47,.25); transform:translateX(2px);}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:hover::after{transform:translateX(110%);}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div[data-selected="true"]{background:linear-gradient(90deg,rgba(224,36,47,.24),rgba(224,36,47,.04)); border-color:rgba(255,69,69,.45);
  box-shadow:0 10px 26px -18px rgba(255,40,40,.9);}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div[data-selected="true"]::before{transform:scaleY(1);}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] [data-testid="stRadioOption"] p{font-size:15px; font-weight:600; transition:color .2s;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div[data-selected="true"] p{color:#fff;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:has([data-focus-visible]){outline:2px solid var(--sm-gold); outline-offset:1px;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] [data-testid="stRadioCaption"]{margin:2px 0 0 !important; padding:0 !important;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] [data-testid="stRadioCaption"] p{font-size:11.5px; color:var(--sm-muted);}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div[data-selected="true"] [data-testid="stRadioCaption"] p{color:#e6b8b8;}
.sm-pagehead{margin:10px 0 6px; animation:smRowIn .5s both;}
.sm-pagehead h2{margin:0 !important; padding:0 0 8px !important; font-size:1.9rem !important; position:relative; display:inline-block;}
.sm-pagehead h2::after{content:""; position:absolute; left:0; right:0; bottom:0; height:2px; transform-origin:left; background:linear-gradient(90deg,var(--sm-hot),transparent);
  box-shadow:0 0 10px rgba(255,69,69,.6); animation:smDraw .8s .15s cubic-bezier(.7,0,.2,1) both;}
.sm-pagehead p{margin:6px 0 0 !important; color:var(--sm-muted); font-size:14px;}
.sm-pagehead [data-testid="stHeaderActionElements"]{display:none !important;}

/* ---------- buttons: a blade of light sweeps across on hover ---------- */
[data-testid="stBaseButton-secondary"],[data-testid="stBaseButton-primary"]{position:relative; overflow:hidden;
  transition:transform .2s ease, box-shadow .25s ease, border-color .25s ease !important;}
[data-testid="stBaseButton-secondary"] > *,[data-testid="stBaseButton-primary"] > *{position:relative; z-index:1;}
[data-testid="stBaseButton-secondary"]{background:rgba(20,17,22,.82) !important; border:1px solid rgba(224,36,47,.38) !important; color:var(--sm-paper) !important;}
[data-testid="stBaseButton-secondary"]::before,[data-testid="stBaseButton-primary"]::before{content:""; position:absolute; inset:0;
  background:linear-gradient(115deg,transparent 30%,rgba(255,80,80,.38) 50%,transparent 70%); transform:translateX(-120%);
  transition:transform .65s cubic-bezier(.2,.8,.2,1);}
[data-testid="stBaseButton-secondary"]:hover::before,[data-testid="stBaseButton-primary"]:hover::before{transform:translateX(120%);}
[data-testid="stBaseButton-secondary"]:hover{border-color:var(--sm-hot) !important; color:#fff !important; transform:translateY(-1px);
  box-shadow:0 0 0 1px rgba(255,69,69,.25),0 10px 30px -12px rgba(224,36,47,.7);}
[data-testid="stBaseButton-primary"]{background:linear-gradient(135deg,#a8101a,#e0242f 55%,#ff4d3f) !important; border:1px solid #ff6156 !important;
  color:#fff !important; box-shadow:0 10px 30px -12px rgba(255,40,40,.85), inset 0 1px 0 rgba(255,255,255,.25);}
[data-testid="stBaseButton-primary"]::before{background:linear-gradient(115deg,transparent 35%,rgba(255,255,255,.35) 50%,transparent 65%);
  animation:smShine 4s ease-in-out infinite;}
[data-testid="stBaseButton-primary"]:hover{transform:translateY(-1px); box-shadow:0 14px 36px -10px rgba(255,40,40,.95), inset 0 1px 0 rgba(255,255,255,.3);}
[data-testid="stBaseButton-secondary"]:active,[data-testid="stBaseButton-primary"]:active{transform:translateY(1px) scale(.99);}

/* ---------- inputs, tables, images ---------- */
[data-baseweb="select"] > div,[data-baseweb="textarea"],[data-baseweb="input"]{border-color:rgba(224,36,47,.28) !important; transition:border-color .2s, box-shadow .2s;}
[data-baseweb="select"] > div:hover,[data-baseweb="textarea"]:hover{border-color:rgba(255,69,69,.6) !important;}
[data-baseweb="textarea"]:focus-within,[data-baseweb="select"] > div:focus-within{box-shadow:0 0 0 3px rgba(224,36,47,.22);}
[data-testid="stDataFrame"]{border:1px solid var(--sm-line); border-radius:10px; overflow:hidden; box-shadow:0 18px 40px -26px rgba(0,0,0,.9);}
[data-testid="stImage"] img{border-radius:10px; border:1px solid rgba(224,36,47,.3); box-shadow:0 22px 50px -26px rgba(224,36,47,.65);}
[data-testid="stAlert"]{border-radius:10px;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] a{color:var(--sm-hot);}

/* ---------- live feed ---------- */
.feed{font-family:var(--sm-mono); font-size:12.5px; line-height:1.45;}
.row{position:relative; overflow:hidden; padding:8px 12px 8px 13px; margin:5px 0; border-radius:8px; color:var(--sm-paper);
  border:1px solid var(--sm-line); border-left:3px solid #6b6b73;
  background:radial-gradient(420px circle at var(--mx) var(--my),rgba(224,36,47,.10),transparent 45%) fixed, rgba(255,255,255,.028);
  transition:transform .2s ease, background-color .2s ease;}
.row:hover{transform:translateX(3px); background-color:rgba(255,255,255,.055);}
.row .why{color:var(--sm-muted); font-size:11.5px;}
.low{border-left-color:var(--sm-green);} .grey{border-left-color:var(--sm-amber);}
.high{border-left-color:var(--sm-hot); background-color:rgba(224,36,47,.08); box-shadow:inset 0 0 0 1px rgba(224,36,47,.2);}
.decoy{border-left-color:var(--sm-violet); background-color:rgba(176,124,255,.07); box-shadow:inset 0 0 0 1px rgba(176,124,255,.2);}
.bait{border-left:3px dashed var(--sm-violet);}
.badge{display:inline-block; padding:1px 8px; border-radius:999px; font-size:10.5px; font-weight:700; margin-left:8px; letter-spacing:.06em; border:1px solid currentColor;}
.b-ok{background:rgba(67,201,127,.12); color:#72e2a3;} .b-bad{background:rgba(255,69,69,.15); color:#ff8080; box-shadow:0 0 14px -3px rgba(255,69,69,.7);}
.b-vote{background:rgba(240,180,41,.12); color:#f7cc60;} .b-freeze{background:rgba(176,124,255,.15); color:#d2b5ff; box-shadow:0 0 14px -3px rgba(176,124,255,.7);}
.enter > .row{animation:smRowIn .5s cubic-bezier(.2,.9,.25,1) both;}
.enter > .row::after{content:""; position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(100deg,transparent 35%,rgba(255,70,70,.35) 50%,transparent 65%); transform:translateX(-110%); animation:smCut .75s .05s ease-out forwards;}
.enter .b-bad,.enter .b-freeze,.enter .b-vote{animation:smStamp .45s .25s cubic-bezier(.3,1.6,.5,1) both;}

/* ---------- column heads ---------- */
.sm-colhead{display:flex; align-items:baseline; gap:12px; margin:6px 0 2px;}
.sm-colhead h3{margin:0 !important; padding:0 !important; font-size:1.65rem !important;}
.sm-colhead .kj{font-family:var(--sm-brush); font-size:1.5rem; color:var(--sm-red); text-shadow:0 0 18px rgba(224,36,47,.6);}
.sm-colhead.plain .kj{color:#8d8890; text-shadow:none;}
.sm-colhead .note{font-size:12px; color:var(--sm-muted); margin-left:auto;}

/* ---------- outcome cards ---------- */
.sm-verdict{margin-top:12px; padding:14px 16px; border-radius:12px; border:1px solid var(--sm-line); background:var(--sm-panel); animation:smRowIn .6s both;}
.sm-verdict.plain{border-color:rgba(255,69,69,.35); box-shadow:0 0 0 1px rgba(255,69,69,.08), 0 20px 40px -30px rgba(255,40,40,.8);}
.sm-verdict .line{font-size:15px;}
.leak{display:flex; gap:10px; align-items:flex-start; color:#ff8a8a; font-weight:600; padding:6px 0 0; animation:smRowIn .5s both;}
.leak:nth-child(3){animation-delay:.12s} .leak:nth-child(4){animation-delay:.24s} .leak:nth-child(5){animation-delay:.36s}
.leak .x{flex:none; width:20px; height:20px; border-radius:5px; background:var(--sm-red); color:#fff; display:grid; place-items:center; font-size:12px; box-shadow:0 0 12px rgba(255,40,40,.6);}
.sm-verdict.win{border-color:rgba(201,164,92,.45); background:linear-gradient(135deg,rgba(224,36,47,.12),rgba(20,17,22,.85) 55%);
  box-shadow:0 22px 50px -30px rgba(224,36,47,.9);}
.sm-stats{display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:12px 0 4px !important; padding:0 !important; list-style:none;}
.sm-stats li{padding:10px 12px; border-radius:10px; background:rgba(0,0,0,.35); border:1px solid var(--sm-line); animation:smRowIn .5s both;}
.sm-stats li:nth-child(2){animation-delay:.1s} .sm-stats li:nth-child(3){animation-delay:.2s}
.sm-stats b{display:block; font-family:var(--sm-serif); font-size:28px; line-height:1.1; color:var(--sm-paper);}
.sm-stats li.good b{color:#72e2a3;} .sm-stats li.red b{color:var(--sm-hot); text-shadow:0 0 18px rgba(255,69,69,.5);}
.sm-stats span{display:block; margin-top:4px; font-size:12px; line-height:1.3; color:var(--sm-muted);}
.sm-flag{margin-top:8px; padding:8px 10px; border-radius:8px; background:rgba(224,36,47,.10); border:1px solid rgba(224,36,47,.3);}
.sm-flag code{color:#ffb1b1; background:rgba(0,0,0,.4);}
@media (max-width:640px){.sm-stats{grid-template-columns:1fr;}}

/* ---------- two views ---------- */
.agent-block{padding:6px 10px; margin:3px 0; border-radius:6px; font-size:13px; background:rgba(255,255,255,.03); border-left:3px solid transparent; transition:transform .2s;}
.agent-block:hover{transform:translateX(3px);}
.agent-block i{color:var(--sm-muted);}
.tag-hidden{background:rgba(255,69,69,.13); border-left-color:var(--sm-hot);}
.tag-bot_only{background:rgba(176,124,255,.13); border-left-color:var(--sm-violet);}
.tag-unverified{background:rgba(240,180,41,.11); border-left-color:var(--sm-amber);}
.tag-instruction{background:rgba(90,155,255,.12); border-left-color:var(--sm-blue);}
.sm-viewhead{font-family:var(--sm-serif); font-size:16px; margin:4px 0 8px;}
.sm-viewhead .kj{font-family:var(--sm-brush); color:var(--sm-red); margin-right:8px;}

/* ---------- orb loader ---------- */
.sm-loader{position:relative; overflow:hidden; display:flex; align-items:center; gap:16px; padding:14px 16px; margin:8px 0;
  border-radius:14px; border:1px solid rgba(224,36,47,.35); background:linear-gradient(90deg,rgba(224,36,47,.12),rgba(18,15,20,.7));}
.sm-loader::after{content:""; position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(100deg,transparent 40%,rgba(255,80,80,.14) 50%,transparent 60%); animation:smSweep 1.8s linear infinite;}
.sm-orb{position:relative; width:64px; height:64px; flex:none;}
.sm-orb .ring{position:absolute; inset:0; border-radius:50%; border:2px solid transparent;}
.sm-orb .r1{border-top-color:var(--sm-hot); border-right-color:rgba(255,69,69,.3); animation:smSpin 1.1s linear infinite;}
.sm-orb .r2{inset:7px; border-bottom-color:var(--sm-gold); border-left-color:rgba(201,164,92,.3); animation:smSpin 1.7s linear infinite reverse;}
.sm-orb .r3{inset:-7px; border:1px dashed rgba(255,69,69,.35); animation:smSpin 7s linear infinite;}
.sm-orb .blade{position:absolute; inset:-7px; animation:smSpin 2.2s cubic-bezier(.65,.05,.35,.95) infinite;}
.sm-orb .blade::before{content:""; position:absolute; left:50%; top:-3px; width:2px; height:24px; transform:translateX(-50%) rotate(8deg);
  border-radius:2px; background:linear-gradient(#fff,var(--sm-hot) 55%,transparent); box-shadow:0 0 10px #ff4545,0 0 2px #fff;}
.sm-orb .core{position:absolute; inset:15px; border-radius:50%; display:grid; place-items:center; color:#fff; font-family:var(--sm-brush); font-size:17px;
  background:radial-gradient(circle at 35% 30%,#ff9a8a,#e0242f 45%,#4a050c 100%);
  box-shadow:0 0 22px rgba(255,50,50,.85),0 0 60px rgba(224,36,47,.45); animation:smPulse 1.5s ease-in-out infinite;}
.sm-loader .txt{min-width:0; flex:1;}
.sm-loader .txt b{display:block; font-family:var(--sm-serif); font-size:15px; color:var(--sm-paper);}
.sm-loader .txt span{display:block; margin-top:3px; font-family:var(--sm-mono); font-size:12px; color:var(--sm-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.sm-loader .dots::after{content:"…"; display:inline-block; width:1.2em; text-align:left; animation:smDots 1.2s steps(4) infinite; overflow:hidden; vertical-align:bottom;}
.sm-loader.plain{border-color:rgba(255,255,255,.14); background:linear-gradient(90deg,rgba(255,255,255,.05),rgba(18,15,20,.7));}
.sm-loader.plain::after{background:linear-gradient(100deg,transparent 40%,rgba(255,255,255,.07) 50%,transparent 60%);}
.sm-loader.plain .r1{border-top-color:#bdb8b3; border-right-color:rgba(255,255,255,.15);}
.sm-loader.plain .r2{border-bottom-color:#76717a; border-left-color:rgba(255,255,255,.1);}
.sm-loader.plain .r3{border-color:rgba(255,255,255,.15);}
.sm-loader.plain .blade{display:none;}
.sm-loader.plain .core{background:radial-gradient(circle at 35% 30%,#e8e3dd,#6d6a70 50%,#1b1a1e 100%); box-shadow:0 0 16px rgba(255,255,255,.25); color:#111;}

/* ---------- hero ---------- */
.sm-hero{position:relative; border-radius:18px; padding:26px 30px 22px; margin:46px 0 10px; min-height:236px;
  border:1px solid rgba(224,36,47,.28); background:linear-gradient(120deg,rgba(18,8,10,.9),rgba(10,9,12,.75) 60%,rgba(40,6,10,.7));
  box-shadow:0 30px 60px -40px rgba(224,36,47,.8), inset 0 1px 0 rgba(255,255,255,.04);
  transform:perspective(1400px) rotateX(calc(var(--py) * -2.2deg)) rotateY(calc(var(--px) * 3deg)); transition:transform .25s ease-out;}
.sm-hero-frame{position:absolute; inset:0; border-radius:inherit; overflow:hidden; pointer-events:none;}
.sm-hero-frame::before{content:""; position:absolute; inset:0; z-index:1;
  background:radial-gradient(500px circle at var(--mx) var(--my),rgba(255,69,69,.13),transparent 45%) fixed;}
.sm-hero-art{position:absolute; right:0; top:0; bottom:0; width:min(70%,760px); opacity:.95;
  translate:calc(var(--px) * -14px) calc(var(--py) * -6px); transition:translate .3s ease-out;
  -webkit-mask-image:linear-gradient(90deg,transparent,#000 40%); mask-image:linear-gradient(90deg,transparent,#000 40%);}
.sm-hero-art svg{width:100%; height:100%; display:block;}
.sm-hero-art .mist{animation:smMist 9s ease-in-out infinite alternate;}
.sm-hero-body{position:relative; z-index:2; max-width:min(720px, calc(100% - 250px));}

/* the samurai: stands on the banner's floor, head and blade break out of the frame */
.sm-samurai{position:absolute; z-index:3; right:3%; bottom:-1px; width:250px; aspect-ratio:320/420; --f:0;
  translate:calc(var(--px) * 18px) calc(var(--py) * 8px); transition:translate .25s ease-out;}
.sm-samurai svg{width:100%; height:100%; display:block; overflow:visible;
  filter:drop-shadow(0 0 1px rgba(255,140,120,.85)) drop-shadow(0 0 calc(10px + var(--f) * 24px) rgba(224,36,47,calc(.35 + var(--f) * .5)));}
.sm-samurai .s-sun{transform:translate(calc(var(--px) * -16px), calc(var(--py) * -10px)); transition:transform .3s ease-out;}
.sm-samurai .s-sun circle{transform-box:fill-box; transform-origin:center; animation:smSun 6s ease-in-out infinite;}
.sm-samurai .s-head{transform-box:view-box; transform-origin:206px 98px; transform:rotate(calc(var(--px) * 7deg - var(--f) * 4deg)); transition:transform .3s ease-out;}
.sm-samurai .s-robe{transform-box:view-box; transform-origin:210px 206px; animation:smSway 3.2s ease-in-out infinite;}
.sm-samurai .s-flap{transform-box:view-box; transform-origin:150px 300px; animation:smFlap 2.1s ease-in-out infinite;}
.sm-samurai .s-blade{transform-box:view-box; transform-origin:242px 208px;
  transform:rotate(calc(var(--f) * 24deg - var(--py) * 10deg)); transition:transform .35s cubic-bezier(.2,.9,.25,1);}
.sm-samurai .s-glint{stroke-dasharray:9 100; stroke-dashoffset:9; animation:smGlint 3.4s 1s ease-in-out infinite;}
.sm-samurai .s-eye{opacity:calc(.15 + var(--f) * .85);}
body:has([data-test-script-state="running"]) .sm-samurai .s-robe{animation-duration:1.4s;}
body:has([data-test-script-state="running"]) .sm-samurai .s-glint{animation-duration:1.4s;}
.sm-eyebrow{margin:0 0 4px !important; font-size:12px; letter-spacing:.32em; text-transform:uppercase; color:var(--sm-gold);}
.sm-title{margin:0 !important; padding:0 !important; font-family:var(--sm-serif) !important; font-weight:800; font-size:clamp(40px,5.4vw,66px) !important;
  line-height:1.05 !important; letter-spacing:.08em; position:relative; display:inline-block; white-space:nowrap;}
.sm-title::after{content:""; position:absolute; left:0; right:.08em; bottom:-6px; height:2px; transform-origin:left;
  background:linear-gradient(90deg,var(--sm-hot),rgba(255,255,255,.9) 50%,var(--sm-hot) 70%,transparent); box-shadow:0 0 12px var(--sm-hot);
  animation:smDraw 1.1s .6s cubic-bezier(.7,0,.2,1) both;}
.sm-sub{margin:14px 0 12px !important; color:#d8d0c7; font-size:15px; max-width:620px;}
.sm-sub em{color:#fff; font-style:normal; border-bottom:1px solid rgba(255,69,69,.6);}
.sm-layers{display:flex; flex-wrap:wrap; gap:8px; margin:0 !important; padding:0 !important; list-style:none;}
.sm-layers li{margin:0 !important; font-size:12px; padding:5px 10px; border-radius:999px; border:1px solid rgba(224,36,47,.3); background:rgba(0,0,0,.35); color:#e6ddd3;
  transition:transform .2s, border-color .2s, box-shadow .2s, background .2s; cursor:default; animation:smRowIn .5s both;}
.sm-layers li:nth-child(1){animation-delay:.5s} .sm-layers li:nth-child(2){animation-delay:.58s} .sm-layers li:nth-child(3){animation-delay:.66s}
.sm-layers li:nth-child(4){animation-delay:.74s} .sm-layers li:nth-child(5){animation-delay:.82s}
.sm-layers li b{color:var(--sm-hot); margin-right:6px; font-family:var(--sm-mono);}
.sm-layers li:hover{transform:translateY(-2px); border-color:var(--sm-hot); background:rgba(224,36,47,.14); box-shadow:0 8px 20px -10px rgba(255,69,69,.8);}
@media (max-width:900px){.sm-samurai{width:190px;} .sm-hero-body{max-width:calc(100% - 150px);}}
@media (max-width:640px){.sm-hero{padding:20px 18px; margin-top:70px;} .sm-hero-art{width:100%; opacity:.45;}
  .sm-samurai{width:132px; right:0;} .sm-hero-body{max-width:100%;} .sm-sub,.sm-layers{margin-right:104px !important;}}

/* cursor-reactive letters: --f (0..1) is set from the cursor distance */
.sm-react .ch{display:inline-block; --f:0; animation:smLetter .8s calc(var(--i) * 55ms + .15s) cubic-bezier(.2,.9,.25,1) both;
  translate:0 calc(var(--f) * -12px); scale:calc(1 + var(--f) * .22); rotate:calc(var(--f) * var(--tilt, 0deg));
  color:color-mix(in oklab, var(--sm-hot) calc(var(--f) * 100%), var(--sm-paper));
  text-shadow:0 0 calc(var(--f) * 26px) rgba(255,50,50,calc(var(--f) * .95)); transition:color .15s;}
.sm-react .ch.sp{width:.3em;}

/* ---------- sidebar brand ---------- */
.sm-brand{display:flex; align-items:center; gap:12px; margin:0 0 4px;}
.sm-brand svg{flex:none; filter:drop-shadow(0 0 10px rgba(224,36,47,.5));}
.sm-brand svg .spin{transform-origin:24px 24px; animation:smSpin 14s linear infinite;}
.sm-brand:hover svg .blades{animation:smFlash .6s ease;}
.sm-brand-name{font-family:var(--sm-serif); font-weight:800; font-size:28px; letter-spacing:.06em; line-height:1.1;}
.sm-brand-sub{font-size:12px; color:var(--sm-muted);}
.sm-mem{display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:10px; border:1px solid rgba(224,36,47,.25); background:rgba(0,0,0,.3); font-size:14px;}
.sm-mem .dot{width:9px; height:9px; border-radius:50%; background:var(--sm-hot); box-shadow:0 0 10px var(--sm-hot); animation:smPulse 2s ease-in-out infinite;}
.sm-mem b{color:#fff;}

/* ---------- background layer (drawn by the script) ---------- */
.sm-fx{position:fixed; inset:0; z-index:-1; pointer-events:none; overflow:hidden;}
.sm-fx canvas{position:absolute; inset:0;}
.sm-fx .moon{position:absolute; width:52vmin; height:52vmin; right:-10vmin; top:-14vmin; border-radius:50%;
  background:radial-gradient(circle at 42% 42%,rgba(255,75,60,.30),rgba(224,36,47,.10) 45%,transparent 70%); filter:blur(8px);
  translate:calc(var(--px) * -36px) calc(var(--py) * -22px);}
.sm-fx .wm{position:absolute; left:2vw; bottom:-8vh; font-family:var(--sm-brush); font-size:44vmin; line-height:1; color:rgba(224,36,47,.045);
  translate:calc(var(--px) * 46px) calc(var(--py) * 26px); user-select:none;}
.sm-bar{position:fixed; left:0; right:0; top:0; height:2px; z-index:1000000; pointer-events:none; opacity:0; transition:opacity .3s;
  background:linear-gradient(90deg,transparent,var(--sm-hot),#fff,var(--sm-hot),transparent) no-repeat; background-size:35% 100%;}
body:has([data-test-script-state="running"]) .sm-bar{opacity:1; animation:smBar 1.1s linear infinite;}
body:has([data-test-script-state="running"]) .sm-fx .moon{animation:smPulse 1.4s ease-in-out infinite;}

/* ---------- splash (first load) ---------- */
.sm-splash{position:fixed; inset:0; z-index:1000001; cursor:pointer;}
.sm-splash .half{position:absolute; inset:0; overflow:hidden; background:radial-gradient(circle at 50% 46%,#22070a,#050506 68%);
  transition:transform .95s cubic-bezier(.75,0,.2,1);}
.sm-splash .a{clip-path:polygon(0 0,100% 0,100% 35%,0 69%);} .sm-splash .b{clip-path:polygon(0 69%,100% 35%,100% 100%,0 100%);}
.sm-splash.out .a{transform:translate(-6%,-105%);} .sm-splash.out .b{transform:translate(6%,105%);}
.sm-splash .in{position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px;}
.sm-splash .sun{width:190px; height:190px; border-radius:50%; display:grid; place-items:center;
  background:radial-gradient(circle at 40% 35%,#ff6a55,#e0242f 50%,#8f0d14); box-shadow:0 0 80px rgba(224,36,47,.75),0 0 200px rgba(224,36,47,.35);
  animation:smPop .7s cubic-bezier(.2,1.3,.4,1) both;}
.sm-splash .sun span{font-family:var(--sm-brush); font-size:118px; line-height:1; color:#0b0a0c; animation:smFade .6s .3s both;}
.sm-splash .word{font-family:var(--sm-serif); font-weight:800; font-size:clamp(34px,6vw,64px); color:var(--sm-paper); letter-spacing:.38em; padding-left:.38em;
  animation:smWord 1s .35s cubic-bezier(.2,.9,.25,1) both;}
.sm-splash .tag{font-size:12px; letter-spacing:.3em; text-transform:uppercase; color:var(--sm-gold); animation:smFade .6s .8s both;}
.sm-splash .cut{position:absolute; left:-2%; top:69%; height:3px; width:var(--len); transform-origin:0 50%; transform:rotate(var(--ang)) scaleX(0);
  background:linear-gradient(90deg,transparent,#fff 15%,#fff 85%,transparent); box-shadow:0 0 14px #ff4545,0 0 3px #fff;
  animation:smSlash .32s 1.25s cubic-bezier(.8,0,.3,1) forwards;}
.sm-splash.out .cut{opacity:0; transition:opacity .3s;}

@keyframes smFade{from{opacity:0}to{opacity:1}}
@keyframes smRowIn{from{opacity:0; transform:translateY(8px) scale(.985); filter:blur(3px);}to{opacity:1; transform:none; filter:none;}}
@keyframes smCut{to{transform:translateX(110%);}}
@keyframes smStamp{from{transform:scale(2.2) rotate(-12deg); opacity:0;}to{transform:none; opacity:1;}}
@keyframes smSpin{to{transform:rotate(360deg);}}
@keyframes smPulse{0%,100%{transform:scale(1); filter:brightness(1);}50%{transform:scale(1.07); filter:brightness(1.25);}}
@keyframes smSweep{from{transform:translateX(-100%);}to{transform:translateX(100%);}}
@keyframes smDots{from{width:0}to{width:1.2em}}
@keyframes smShine{0%,60%{transform:translateX(-120%);}85%,100%{transform:translateX(120%);}}
@keyframes smLetter{from{opacity:0; transform:translateY(.5em) rotate(6deg); filter:blur(6px);}to{opacity:1; transform:none; filter:none;}}
@keyframes smDraw{from{transform:scaleX(0);}to{transform:scaleX(1);}}
@keyframes smSway{0%,100%{transform:skewX(-1.5deg);}50%{transform:skewX(3.5deg);}}
@keyframes smFlap{0%,100%{transform:rotate(0deg) translateX(0);}50%{transform:rotate(-4deg) translateX(-5px);}}
@keyframes smGlint{0%{stroke-dashoffset:9;}45%,100%{stroke-dashoffset:-100;}}
@keyframes smMist{from{transform:translateX(-12px);}to{transform:translateX(16px);}}
@keyframes smSun{0%,100%{transform:scale(1);}50%{transform:scale(1.035);}}
@keyframes smFlash{50%{filter:brightness(2) drop-shadow(0 0 6px #fff);}}
@keyframes smBar{from{background-position:-40% 0;}to{background-position:140% 0;}}
@keyframes smPop{from{transform:scale(.2); opacity:0;}to{transform:none; opacity:1;}}
@keyframes smWord{from{opacity:0; letter-spacing:.9em; filter:blur(8px);}to{opacity:1; letter-spacing:.38em; filter:none;}}
@keyframes smSlash{to{transform:rotate(var(--ang)) scaleX(1);}}

@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{animation-duration:.001ms !important; animation-delay:0s !important; animation-iteration-count:1 !important; transition-duration:.001ms !important;}
  .sm-hero,.sm-hero-art,.sm-samurai,.sm-samurai *,.sm-fx .moon,.sm-fx .wm{transform:none !important; translate:none !important;}
  .sm-react .ch{translate:none; scale:none; rotate:none;}
  .sm-splash{display:none;}
}
""".replace("__FONTS__", FONTS)

# Runs once in the page itself (not in an iframe): background particles that scatter away from the cursor,
# a soft glow and blade trail behind the pointer, a slash on click, letters that lift as the cursor nears,
# and a splash screen on first load. Decorative layers are aria-hidden and ignore pointer events.
JS = r"""
(function(){
  const W = window, D = document;
  if (W.__smFx) return; W.__smFx = true;
  const reduce = W.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = W.matchMedia('(pointer: fine)').matches;
  const root = D.documentElement;

  // ---------- splash ----------
  if (!reduce) {
    const inner = '<div class="in"><div class="sun"><span>侍</span></div><div class="word">SCAMURAI</div>'
                + '<div class="tag">A samurai for your shopping agent</div></div>';
    const s = D.createElement('div');
    s.className = 'sm-splash'; s.setAttribute('aria-hidden', 'true');
    s.innerHTML = '<div class="half a">' + inner + '</div><div class="half b">' + inner + '</div>'
      + '<div class="cut"></div>';
    // the cut runs from 69% down the left edge to 35% down the right edge, matching the two halves
    const vw = W.innerWidth, vh = W.innerHeight, dx = vw * 1.04, dy = -0.34 * vh;
    const cut = s.querySelector('.cut');
    cut.style.setProperty('--len', Math.hypot(dx, dy) + 'px');
    cut.style.setProperty('--ang', Math.atan2(dy, dx) + 'rad');
    D.body.appendChild(s);
    let gone = false;
    const done = () => { if (gone) return; gone = true; s.classList.add('out'); setTimeout(() => s.remove(), 1000); };
    setTimeout(done, 1750);
    s.addEventListener('click', done);
    D.addEventListener('keydown', done, {once: true});
  }

  // ---------- layers ----------
  const fx = D.createElement('div');
  fx.className = 'sm-fx'; fx.setAttribute('aria-hidden', 'true');
  fx.innerHTML = '<div class="moon"></div><div class="wm">侍</div><canvas></canvas>';
  D.body.appendChild(fx);
  const bar = D.createElement('div'); bar.className = 'sm-bar'; bar.setAttribute('aria-hidden', 'true');
  D.body.appendChild(bar);
  const cv = fx.querySelector('canvas'), ctx = cv.getContext('2d');
  let w = 0, h = 0;
  function size(){
    const dpr = Math.min(W.devicePixelRatio || 1, 2);
    w = W.innerWidth; h = W.innerHeight;
    cv.width = w * dpr; cv.height = h * dpr; cv.style.width = w + 'px'; cv.style.height = h + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  size();

  // ---------- pointer ----------
  const m = {x: w * .5, y: h * .35, sx: w * .5, sy: h * .35, on: false};
  const trail = [], slashes = [];
  W.addEventListener('pointermove', e => {
    m.x = e.clientX; m.y = e.clientY; m.on = true;
    if (e.pointerType === 'mouse') { trail.push({x: m.x, y: m.y, t: performance.now()}); if (trail.length > 28) trail.shift(); }
  }, {passive: true});
  D.addEventListener('mouseleave', () => { m.on = false; });
  W.addEventListener('pointerdown', e => {
    if (reduce || e.pointerType !== 'mouse') return;
    slashes.push({x: e.clientX, y: e.clientY, a: -0.62 + (Math.random() - .5) * .5, t: performance.now()});
  }, {passive: true});

  // ---------- petals and embers ----------
  const ps = [];
  function spawn(p, fresh){
    p.x = fresh ? Math.random() * w : -20 + Math.random() * w * .7;
    p.y = fresh ? Math.random() * h : -20;
    p.vx = .15 + Math.random() * .35; p.vy = .25 + Math.random() * .55;
    p.r = 2 + Math.random() * 3.6; p.rot = Math.random() * 6.28; p.vr = (Math.random() - .5) * .04;
    p.ph = Math.random() * 6.28; p.ember = Math.random() < .35; p.a = .25 + Math.random() * .5;
    p.c = p.ember ? '255,110,70' : (Math.random() < .5 ? '224,36,47' : '255,82,82');
    return p;
  }
  function fill(){
    const n = Math.round(Math.min(fine ? 90 : 40, w * h / 20000));
    while (ps.length < n) ps.push(spawn({}, true));
    ps.length = n;
  }
  fill();
  W.addEventListener('resize', () => { size(); fill(); if (reduce) draw(performance.now()); });

  // ---------- cursor-reactive letters ----------
  let letters = [], lastScan = 0;
  function scan(){
    letters = Array.from(D.querySelectorAll('.sm-react .ch, [data-prox]')).map(el => {
      const r = el.getBoundingClientRect();
      return {el, x: r.left + r.width / 2, y: r.top + r.height / 2, f: el.__f || 0, R: +(el.dataset.prox || 170)};
    });
  }
  D.addEventListener('scroll', () => { lastScan = 0; }, {capture: true, passive: true});

  function draw(now){
    ctx.clearRect(0, 0, w, h);
    const running = !!D.querySelector('[data-test-script-state="running"]');
    const speed = reduce ? 0 : (running ? 2.4 : 1);
    m.sx += (m.x - m.sx) * .14; m.sy += (m.y - m.sy) * .14;
    root.style.setProperty('--mx', m.sx.toFixed(1) + 'px');
    root.style.setProperty('--my', m.sy.toFixed(1) + 'px');
    root.style.setProperty('--px', (m.sx / w - .5).toFixed(3));
    root.style.setProperty('--py', (m.sy / h - .5).toFixed(3));

    if (fine && m.on && !reduce) {
      const g = ctx.createRadialGradient(m.sx, m.sy, 0, m.sx, m.sy, 240);
      g.addColorStop(0, 'rgba(224,36,47,.17)'); g.addColorStop(1, 'rgba(224,36,47,0)');
      ctx.fillStyle = g; ctx.fillRect(m.sx - 240, m.sy - 240, 480, 480);
    }

    for (const p of ps) {
      if (speed) {
        p.ph += .02 * speed;
        p.x += (p.vx + Math.sin(p.ph) * .45) * speed; p.y += p.vy * speed; p.rot += p.vr * speed;
        if (m.on) {
          const dx = p.x - m.sx, dy = p.y - m.sy, d2 = dx * dx + dy * dy, R = 140;
          if (d2 < R * R) { const d = Math.sqrt(d2) || 1, f = (R - d) / R; p.x += dx / d * f * 5; p.y += dy / d * f * 5; p.rot += f * .2; }
        }
        if (p.y > h + 20 || p.x > w + 20) spawn(p, false);
      }
      if (p.ember) {
        ctx.fillStyle = 'rgba(' + p.c + ',' + (p.a * .25).toFixed(3) + ')';
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 1.3, 0, 6.283); ctx.fill();
        ctx.fillStyle = 'rgba(255,190,150,' + p.a.toFixed(3) + ')';
        ctx.beginPath(); ctx.arc(p.x, p.y, .9, 0, 6.283); ctx.fill();
      } else {
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot);
        ctx.fillStyle = 'rgba(' + p.c + ',' + p.a.toFixed(3) + ')';
        ctx.beginPath(); ctx.ellipse(0, 0, p.r * 1.7, p.r * .75, 0, 0, 6.283); ctx.fill();
        ctx.restore();
      }
    }

    if (fine && !reduce) {
      while (trail.length && now - trail[0].t > 170) trail.shift();
      for (let i = 1; i < trail.length; i++) {
        const k = i / trail.length;
        ctx.strokeStyle = 'rgba(255,' + Math.round(70 + 150 * k) + ',' + Math.round(70 + 150 * k) + ',' + (k * .7).toFixed(3) + ')';
        ctx.lineWidth = k * 3.2; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(trail[i - 1].x, trail[i - 1].y); ctx.lineTo(trail[i].x, trail[i].y); ctx.stroke();
      }
      for (let i = slashes.length - 1; i >= 0; i--) {
        const s = slashes[i], age = (now - s.t) / 420;
        if (age >= 1) { slashes.splice(i, 1); continue; }
        const grow = Math.min(1, age * 3.2), L = 90 * grow, cx = Math.cos(s.a), sy = Math.sin(s.a), fade = 1 - age;
        ctx.lineCap = 'round';
        ctx.strokeStyle = 'rgba(255,69,69,' + (fade * .8).toFixed(3) + ')'; ctx.lineWidth = 6 * fade;
        ctx.beginPath(); ctx.moveTo(s.x - cx * L, s.y - sy * L); ctx.lineTo(s.x + cx * L, s.y + sy * L); ctx.stroke();
        ctx.strokeStyle = 'rgba(255,255,255,' + fade.toFixed(3) + ')'; ctx.lineWidth = 1.6 * fade;
        ctx.beginPath(); ctx.moveTo(s.x - cx * L, s.y - sy * L); ctx.lineTo(s.x + cx * L, s.y + sy * L); ctx.stroke();
      }
    }

    if (!reduce && fine) {
      if (now - lastScan > 350) { scan(); lastScan = now; }
      for (const L of letters) {
        let f = 0;
        if (m.on) { const d = Math.hypot(L.x - m.sx, L.y - m.sy); f = Math.max(0, 1 - d / L.R); f = f * f * (3 - 2 * f); }
        if (Math.abs(f - L.f) > .004) { L.f = f; L.el.__f = f; L.el.style.setProperty('--f', f.toFixed(3)); }
      }
    }
  }

  if (reduce) { draw(performance.now()); return; }
  function loop(now){ if (!D.hidden) draw(now); requestAnimationFrame(loop); }
  requestAnimationFrame(loop);
})();
"""

LAYERS = [
    ("01", "Two views", "Each page is read as a person sees it and as a bot fetches it. Text only the bot sees is taken out."),
    ("02", "Source labels", "Every detail of an action is labelled user, tool or seller, in code. Unknown values fail closed."),
    ("03", "Firewall", "Fixed rules no vote can overrule: paying, personal details and seller links."),
    ("04", "Voters", "Three judges vote on medium-risk actions."),
    ("05", "Decoys", "Fake tools no honest page asks for. Touching one freezes the session."),
]

HERO_ART = " ".join("""<svg viewBox="0 0 640 200" preserveAspectRatio="xMaxYMax slice" aria-hidden="true">
<defs>
 <linearGradient id="smMtA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a0b0f"/><stop offset="1" stop-color="#0c0a0d"/></linearGradient>
 <linearGradient id="smMtB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#14090c"/><stop offset="1" stop-color="#060507"/></linearGradient>
</defs>
<path d="M120 200 L240 104 L292 136 L370 76 L440 126 L500 100 L640 168 L640 200 Z" fill="url(#smMtA)"/>
<g class="mist" stroke="rgba(255,90,90,.16)" stroke-width="2" stroke-linecap="round">
 <line x1="230" y1="140" x2="420" y2="140"/><line x1="300" y1="152" x2="520" y2="152"/><line x1="380" y1="128" x2="470" y2="128"/></g>
<path d="M200 200 L300 156 L350 172 L430 134 L510 166 L570 146 L640 178 L640 200 Z" fill="url(#smMtB)"/>
</svg>""".split())

# An original samurai silhouette: topknot, robe blowing in the wind, katana held low, red sun behind.
SAMURAI = " ".join("""<svg viewBox="0 0 320 420" aria-hidden="true" focusable="false">
<defs>
 <radialGradient id="smSun2" cx="42%" cy="38%" r="62%"><stop offset="0" stop-color="#ff6a55"/><stop offset=".55" stop-color="#e0242f"/><stop offset="1" stop-color="#7d0a12"/></radialGradient>
 <linearGradient id="smRobe" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e01b31"/><stop offset=".5" stop-color="#9c0e19"/><stop offset="1" stop-color="#140608"/></linearGradient>
 <linearGradient id="smUpper" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c3121f"/><stop offset=".7" stop-color="#4a070d"/><stop offset="1" stop-color="#120507"/></linearGradient>
 <linearGradient id="smSleeve" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a50f1b"/><stop offset="1" stop-color="#1c0709"/></linearGradient>
 <linearGradient id="smSteel" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#9d97a0"/><stop offset=".6" stop-color="#f3ece2"/><stop offset="1" stop-color="#c9c2bb"/></linearGradient>
 <radialGradient id="smFloor" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="rgba(224,36,47,.55)"/><stop offset="1" stop-color="rgba(224,36,47,0)"/></radialGradient>
</defs>
<g class="s-sun"><circle cx="150" cy="122" r="76" fill="url(#smSun2)"/></g>
<ellipse cx="200" cy="410" rx="120" ry="9" fill="url(#smFloor)"/>
<g class="s-robe">
 <g class="s-flap"><path d="M150 300 C120 330 92 352 54 372 C88 372 112 362 134 346 C116 362 104 378 84 392 C122 386 146 368 162 340 Z" fill="#c1121f"/></g>
 <path d="M182 205 L240 207 C246 250 254 320 268 398 L150 400 C120 398 92 394 62 386 C88 376 104 366 116 352 C98 354 84 360 70 364 C102 334 136 300 154 262 C164 240 174 222 182 205 Z" fill="url(#smRobe)"/>
 <g fill="none" stroke="#0a0405" stroke-width="2.6" stroke-linecap="round" opacity=".85">
  <path d="M206 214 C204 280 200 340 196 398"/><path d="M226 216 C230 280 236 340 240 398"/><path d="M190 228 C176 282 150 330 118 360"/></g>
</g>
<path d="M190 398 h36 q4 0 4 6 v4 h-42 z M236 398 h30 q5 0 5 6 v4 h-37 z" fill="#0b0607"/>
<path d="M196 100 C186 104 176 112 174 126 C172 150 176 180 180 206 L240 208 C240 186 238 160 236 136 C234 118 226 106 214 100 Z" fill="url(#smUpper)"/>
<g stroke="#0a0405" stroke-width="3" stroke-linecap="round" opacity=".8"><path d="M179 132 L204 116"/><path d="M178 160 L206 138"/><path d="M200 104 L213 138 L222 105" fill="none" stroke-width="2.4"/></g>
<path d="M186 110 C168 122 162 150 166 178 C168 196 178 206 192 208 C200 200 210 196 222 200 L242 206 L244 198 C232 190 222 182 214 172 C206 150 202 124 186 110 Z" fill="url(#smSleeve)"/>
<path d="M180 199 L241 201 L242 214 L181 213 Z" fill="#0b0607"/><path d="M181 206 L241 207.5" stroke="#e0242f" stroke-width="1.2"/>
<g class="s-head">
 <path d="M199 86 L212 86 L214 104 L198 104 Z" fill="#0b0607"/>
 <path d="M188 62 C188 44 200 36 212 38 C224 40 230 50 229 62 L233 72 L229 74 C229 80 227 84 223 87 C219 92 212 94 205 93 C196 91 190 82 188 72 Z" fill="#0b0607"/>
 <circle cx="196" cy="33" r="9" fill="#0b0607"/><path d="M191 42 L203 44" stroke="#e0242f" stroke-width="2.2" stroke-linecap="round"/>
 <path d="M190 60 C183 70 185 84 192 92" fill="none" stroke="#0b0607" stroke-width="2"/>
 <circle class="s-eye" cx="222" cy="60" r="1.8" fill="#ff4545"/>
</g>
<g class="s-blade">
 <path d="M238 209 Q130 270 16 352 Q134 281 243 215 Z" fill="url(#smSteel)"/>
 <path class="s-glint" d="M240 212 Q132 276 18 351" pathLength="100" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>
 <line x1="243" y1="205" x2="296" y2="166" stroke="#120608" stroke-width="8" stroke-linecap="round"/>
 <line x1="245" y1="203.5" x2="294" y2="167.5" stroke="#e0242f" stroke-width="5" stroke-dasharray="3 4"/>
 <circle cx="296" cy="166" r="3.6" fill="#c9a45c"/>
 <ellipse cx="240" cy="208" rx="3.6" ry="9.5" transform="rotate(-35 240 208)" fill="#c9a45c"/>
</g>
<ellipse cx="245" cy="203" rx="7.5" ry="6.5" fill="#0b0607"/>
</svg>""".split())

CREST = " ".join("""<svg width="46" height="46" viewBox="0 0 48 48" aria-hidden="true">
<circle cx="24" cy="24" r="22.5" fill="#15070a" stroke="#e0242f" stroke-width="1.5"/>
<circle class="spin" cx="24" cy="24" r="18" fill="none" stroke="rgba(255,69,69,.45)" stroke-width="1" stroke-dasharray="2 3"/>
<g class="blades" stroke-linecap="round">
 <path d="M13 35 Q22 22 36 11" fill="none" stroke="#f3ece2" stroke-width="1.8"/>
 <path d="M35 35 Q26 22 12 11" fill="none" stroke="#f3ece2" stroke-width="1.8"/>
 <line x1="13" y1="35" x2="17.5" y2="30.5" stroke="#e0242f" stroke-width="3.4"/>
 <line x1="35" y1="35" x2="30.5" y2="30.5" stroke="#e0242f" stroke-width="3.4"/>
 <line x1="15.6" y1="28.8" x2="19.2" y2="32.4" stroke="#c9a45c" stroke-width="2"/>
 <line x1="32.4" y1="28.8" x2="28.8" y2="32.4" stroke="#c9a45c" stroke-width="2"/>
</g></svg>""".split())


def esc(s) -> str:
    return html.escape(str(s))


def letters(text: str) -> str:
    """Text whose letters react to the cursor. Screen readers get the plain word once."""
    tilts = ["-6deg", "5deg", "-4deg", "7deg", "-5deg", "4deg"]
    spans = "".join(
        "<span class='ch sp'> </span>" if ch == " " else
        f"<span class='ch' style='--i:{i};--tilt:{tilts[i % len(tilts)]}'>{esc(ch)}</span>"
        for i, ch in enumerate(text))
    return f"<span class='sr-only'>{esc(text)}</span><span class='sm-react' aria-hidden='true'>{spans}</span>"


def inject() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
    # Base64, because Streamlit's sanitiser drops any script whose text contains HTML-like snippets.
    b64 = base64.b64encode(JS.encode()).decode()
    st.html("<script>new Function(new TextDecoder().decode(Uint8Array.from(atob('" + b64 + "'), c => c.charCodeAt(0))))()</script>",
            unsafe_allow_javascript=True)


def hero() -> None:
    chips = "".join(f"<li title='{esc(d)}'><b>{n}</b>{esc(t)}</li>" for n, t, d in LAYERS)
    st.markdown(
        "<section class='sm-hero' aria-label='Scamurai'>"
        f"<div class='sm-hero-frame' aria-hidden='true'><div class='sm-hero-art'>{HERO_ART}</div></div>"
        f"<div class='sm-samurai' data-prox='320' aria-hidden='true'>{SAMURAI}</div>"
        "<div class='sm-hero-body'>"
        "<p class='sm-eyebrow'>The firewall for AI shopping agents</p>"
        f"<h1 class='sm-title'>{letters('SCAMURAI')}</h1>"
        "<p class='sm-sub'>A samurai for your shopping agent. Every action is checked against one question: "
        "<em>did this come from you, or from the seller?</em></p>"
        f"<ul class='sm-layers' aria-label='Five layers of defence'>{chips}</ul>"
        "</div></section>", unsafe_allow_html=True)


def brand() -> None:
    st.markdown(f"<div class='sm-brand'>{CREST}<div><h2 class='sm-brand-name' style='margin:0;padding:0'>{letters('Scamurai')}</h2>"
            "<div class='sm-brand-sub'>A samurai for your shopping agent</div></div></div>", unsafe_allow_html=True)


def side_label(kanji: str, text: str) -> None:
    st.markdown(f"<div class='sm-side-label'><span class='kj' aria-hidden='true'>{kanji}</span>{esc(text)}</div>",
                unsafe_allow_html=True)


def page_head(title: str, caption: str) -> None:
    st.markdown(f"<div class='sm-pagehead'><h2>{esc(title)}</h2><p>{esc(caption)}</p></div>", unsafe_allow_html=True)


def memory_line(threats: int, sellers: int) -> str:
    return (f"<div class='sm-mem'><span class='dot' aria-hidden='true'></span>"
            f"<span>🧠 Memory: <b>{threats}</b> threats, <b>{sellers}</b> sellers</span></div>")


def column_head(title: str, kanji: str, note: str, plain: bool) -> str:
    return (f"<div class='sm-colhead {'plain' if plain else 'guard'}'><span class='kj' aria-hidden='true'>{kanji}</span>"
            f"<h3>{esc(title)}</h3><span class='note'>{esc(note)}</span></div>")


def orb(title: str, step: str = "", plain: bool = False) -> str:
    """The loader shown while an agent works: spinning rings, an orbiting blade and a glowing core."""
    glyph = "無" if plain else "侍"
    return (f"<div class='sm-loader {'plain' if plain else 'guard'}' role='status'>"
            "<div class='sm-orb' aria-hidden='true'><span class='ring r3'></span><span class='ring r1'></span>"
            f"<span class='ring r2'></span><span class='blade'></span><span class='core'>{glyph}</span></div>"
            f"<div class='txt'><b>{esc(title)}<span class='dots' aria-hidden='true'></span></b><span>{esc(step)}</span></div></div>")


def style_chart(fig) -> None:
    """Recolour the scoreboard chart for the dark page (the saved PNG keeps its own look)."""
    ink, paper, muted = "#0f0d11", "#f3ece2", "#aba39b"
    fig.patch.set_facecolor(ink)
    for ax in fig.axes:
        ax.set_facecolor(ink)
        ax.tick_params(colors=muted)
        ax.yaxis.label.set_color(muted)
        ax.title.set_color(paper)
        ax.title.set_fontweight("bold")
        for s in ax.spines.values():
            s.set_color("#3a3238")
        ax.grid(axis="y", color="#ffffff", alpha=.06)
        ax.set_axisbelow(True)
        for cont, col in zip(ax.containers, ["#c9a45c", "#e0242f"]):
            for bar in cont:
                bar.set_color(col)
        leg = ax.legend(frameon=False)
        for t in leg.get_texts():
            t.set_color(paper)
