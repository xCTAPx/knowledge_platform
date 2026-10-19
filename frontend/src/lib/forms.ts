import { FormEvent, KeyboardEvent } from "react";

export function isolateSubmit(handler: (event: FormEvent<HTMLFormElement>) => void) {
  return (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    event.stopPropagation();
    handler(event);
  };
}

export function stopFileEnter(event: KeyboardEvent<HTMLInputElement>) {
  if (event.key === "Enter") {
    event.preventDefault();
    event.stopPropagation();
  }
}
