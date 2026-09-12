import{aV as f,aW as c,aI as y}from"./cicrfwpc.js";import{S as d}from"./Bqpd76b4.js";import"./Dw5cRyJq.js";import"./BKQVsGck.js";import"./D_vXau2e.js";import"./CP305iJ0.js";import"./DiYaDy8a.js";import"./BYlmoOb2.js";function a(o){return o.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&apos;")}const S=f(async o=>{const n=y(),g=n.public?.apiBase||"http://127.0.0.1:8001",l=n.public?.siteUrl||d.url,p=[{path:"/",priority:"1.0",changefreq:"daily"},{path:"/products",priority:"0.9",changefreq:"weekly"},{path:"/cases",priority:"0.8",changefreq:"weekly"},{path:"/about",priority:"0.7",changefreq:"monthly"},{path:"/news",priority:"0.8",changefreq:"daily"},{path:"/contact",priority:"0.6",changefreq:"monthly"},{path:"/privacy",priority:"0.5",changefreq:"yearly"},{path:"/terms",priority:"0.5",changefreq:"yearly"}];let s=[];try{const i=await fetch(`${g}/api/v1/products/sitemap-feed?limit=500`,{headers:{Accept:"application/json"},signal:AbortSignal.timeout(5e3)});if(i.ok){const t=await i.json();s=Array.isArray(t)?t:t?.data||t?.items||[]}}catch{}const m=new Date().toISOString().split("T")[0];let e=`<?xml version="1.0" encoding="UTF-8"?>
`;return e+=`<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
`,e+=`        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
`,e+=`        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
`,p.forEach(i=>{e+=`  <url>
`,e+=`    <loc>${a(l+i.path)}</loc>
`,e+=`    <lastmod>${m}</lastmod>
`,e+=`    <changefreq>${i.changefreq}</changefreq>
`,e+=`    <priority>${i.priority}</priority>
`,e+=`  </url>
`}),s.forEach(i=>{if(!i.slug)return;const t=`${l}/products/${i.slug}`,h=i.updated_at?new Date(i.updated_at).toISOString().split("T")[0]:m;e+=`  <url>
`,e+=`    <loc>${a(t)}</loc>
`,e+=`    <lastmod>${h}</lastmod>
`,e+=`    <changefreq>weekly</changefreq>
`,e+=`    <priority>0.8</priority>
`,i.image_url&&(e+=`    <image:image>
`,e+=`      <image:loc>${a(i.image_url)}</image:loc>
`,e+=`      <image:title>${a(i.name)}</image:title>
`,i.description&&(e+=`      <image:caption>${a(i.description.substring(0,200))}</image:caption>
`),e+=`    </image:image>
`),i.images&&Array.isArray(i.images)&&i.images.forEach(r=>{r.image_url&&(e+=`    <image:image>
`,e+=`      <image:loc>${a(r.image_url)}</image:loc>
`,e+=`      <image:title>${a(r.alt_text||i.name)}</image:title>
`,e+=`    </image:image>
`)}),i.video_url&&(e+=`    <video:video>
`,e+=`      <video:thumbnail_loc>${a(i.video_thumbnail||i.image_url||"")}</video:thumbnail_loc>
`,e+=`      <video:title>${a(i.video_title||i.name)}</video:title>
`,e+=`      <video:description>${a(i.video_description||i.description||i.name)}</video:description>
`,e+=`      <video:content_loc>${a(i.video_url)}</video:content_loc>
`,e+=`    </video:video>
`),e+=`  </url>
`}),e+="</urlset>",c(o,"Content-Type","application/xml; charset=utf-8"),c(o,"Cache-Control","public, max-age=3600, s-maxage=7200"),e});export{S as default};
