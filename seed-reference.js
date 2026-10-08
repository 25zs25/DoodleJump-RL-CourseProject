/* Independent reference: execute unchanged upstream functions; seed their RNG only. */
(() => {
  const originalSetup=setup,originalDraw=draw,originalReset=resetGame;
  let seed=42,state=42,ready=false;
  const rng=()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296;};
  // p5 resizeCanvas() redraws synchronously inside resetGame(). Nested calls
  // must restore the preceding scoped RNG, rather than the browser RNG.
  const seeded=fn=>{const precedingRandom=Math.random;Math.random=rng;try{return fn();}finally{Math.random=precedingRandom;}};
  setup=function(){seeded(originalSetup);ready=true;noLoop();};
  draw=function(){seeded(originalDraw);};
  resetGame=function(){state=seed;seeded(originalReset);};
  globalThis.OriginalReference={ready:()=>ready,rng:()=>({seed,state}),reset(s=42){noLoop();seed=s>>>0;state=seed;seeded(originalReset);},frame(a){if(isOver)return;doodler.vx=a===0?-Doodler.speed:a===2?Doodler.speed:0;if(a!==1)doodler.direction=a===0?0:1;seeded(originalDraw);}};
})();
