import { Brand } from "./Brand";
import { Icon } from "./Icon";
import "./Topbar.css";

export function Topbar({
  nickname,
  onAdd,
  onLogout,
}: {
  nickname: string;
  onAdd: () => void;
  onLogout: () => void;
}) {
  return (
    <>
      <div className="topbar">
        <Brand />
        <div className="actions">
          <button type="button" onClick={onAdd}>
            <Icon name="plus" />
            Add
          </button>
          <button type="button" className="ghost" onClick={onLogout}>
            Log out
          </button>
        </div>
      </div>
      <p className="lede">
        Signed in as <strong>{nickname}</strong>
      </p>
    </>
  );
}
