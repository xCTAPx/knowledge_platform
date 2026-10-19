import { ReactNode } from "react";

export function Compose({ children }: { children: ReactNode }) {
  return <div className="compose">{children}</div>;
}
