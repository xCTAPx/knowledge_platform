import { Brand } from "./Brand";

export function Topbar({ nickname, onLogout }: { nickname: string; onLogout: () => void }) {
  return (
    <>
      <div className="topbar">
        <Brand />
        <button type="button" className="ghost" onClick={onLogout}>
          Log out
        </button>
      </div>
      <p className="lede">
        Signed in as <strong>{nickname}</strong>
      </p>
    </>
  );
}
