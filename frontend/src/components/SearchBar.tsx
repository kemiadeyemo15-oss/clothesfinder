import { useRef, useState } from "react";

interface Props {
  onSearch: (text: string, image: string | null) => void;
  busy: boolean;
}

export function SearchBar({ onSearch, busy }: Props) {
  const [text, setText] = useState("");
  const [image, setImage] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) {
      setImage(null);
      setFileName(null);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setImage(reader.result as string);
      setFileName(f.name);
    };
    reader.readAsDataURL(f);
  }

  function go() {
    if (!text.trim() && !image) return;
    onSearch(text.trim(), image);
  }

  return (
    <div className="panel">
      <div className="row">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) go();
          }}
          placeholder="e.g. oversized cream wool coat, belted, under £200"
        />
        <div className="controls">
          <label className={`file${fileName ? " has" : ""}`}>
            {fileName ? `✓ ${fileName}` : "+ add a photo / screenshot"}
            <input ref={fileRef} type="file" accept="image/*" onChange={onFile} />
          </label>
          <button onClick={go} disabled={busy}>
            {busy ? "Searching…" : "Search"}
          </button>
        </div>
      </div>
    </div>
  );
}
