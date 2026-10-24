export function letterStream(onText: (text: string) => void) {
  let shown = "";
  let rest = "";
  let closed = false;
  let id = 0;

  function paint() {
    if (!rest) return;
    shown += rest[0];
    rest = rest.slice(1);
    onText(shown);
  }

  function tick() {
    paint();
    if (rest || !closed) id = requestAnimationFrame(tick);
  }

  id = requestAnimationFrame(tick);

  return {
    push(chunk: string) {
      rest += chunk;
    },
    end() {
      closed = true;
      return new Promise<void>((resolve) => {
        const drain = () => {
          paint();
          if (rest) requestAnimationFrame(drain);
          else resolve();
        };
        drain();
      });
    },
    stop() {
      closed = true;
      cancelAnimationFrame(id);
    },
  };
}
