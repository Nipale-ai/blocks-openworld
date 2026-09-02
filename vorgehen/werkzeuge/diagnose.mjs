import { chromium } from '/Users/niklasplenz/pyriq/content-engine/ki-kanal/capture/node_modules/playwright/index.mjs';
const b = await chromium.launch({ channel:'chrome', args:['--mute-audio','--use-gl=angle','--use-angle=metal'] });
const p = await b.newPage({ viewport:{width:900,height:600} });
await p.goto('file://' + process.cwd() + '/game.html');
for (let i=0;i<200;i++){ await p.waitForTimeout(250);
  if (/ready|ERROR/.test(await p.textContent('#load-text').catch(()=>''))) break; }
await p.mouse.click(450,400); await p.waitForTimeout(1500);
await p.evaluate(()=>{ window.__dbg.setHeadless(true); window.__dbg.teleport(-40,-25,0); });
await p.waitForTimeout(1000);
const lies = async (w) => {
  await p.evaluate(x=>window.__dbg.select(x), w);
  await p.waitForTimeout(2500);            // Daempfung ausschwingen lassen
  return p.evaluate(() => {
    const P = window.__G.player, b = P.bones, r = {};
    for (const n of ['UpperArm_R','Forearm_R','Hand_R','UpperArm_L','Forearm_L','Hand_L','Chest','Head'])
      if (b[n]) r[n] = [+b[n].rotation.x.toFixed(3), +b[n].rotation.y.toFixed(3), +b[n].rotation.z.toFixed(3)];
    return r;
  });
};
const a = await lies(0), c = await lies(1), d = await lies(2);
console.log('KNOCHEN-ROTATIONEN je Waffe (x,y,z in rad)');
for (const n of Object.keys(a)) {
  const diff = (u,v) => Math.max(...u.map((x,i)=>Math.abs(x-v[i]))).toFixed(3);
  console.log(`${n.padEnd(12)} pistole ${JSON.stringify(a[n])}`);
  console.log(`${''.padEnd(12)} mg      ${JSON.stringify(c[n])}   Δ zu Pistole: ${diff(a[n],c[n])}`);
  console.log(`${''.padEnd(12)} rakete  ${JSON.stringify(d[n])}   Δ zu Pistole: ${diff(a[n],d[n])}`);
}
await b.close();
