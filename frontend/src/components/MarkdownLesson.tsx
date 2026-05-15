import styles from "./MarkdownLesson.module.css";

type MarkdownLessonProps = {
  markdown: string;
};

type ListMode = "ul" | "ol";

export default function MarkdownLesson({ markdown }: MarkdownLessonProps) {
  const blocks = parseBlocks(markdown);

  return (
    <article className={styles.lesson}>
      {blocks.map((block, index) => {
        if (block.type === "heading") return renderHeading(block.level, block.text, index);
        if (block.type === "list") return renderList(block.mode, block.items, index);
        return (
          <p key={index}>
            {renderInline(block.text)}
          </p>
        );
      })}
    </article>
  );
}

function parseBlocks(markdown: string) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks: Array<
    | { type: "heading"; level: 1 | 2 | 3; text: string }
    | { type: "list"; mode: ListMode; items: string[] }
    | { type: "paragraph"; text: string }
  > = [];
  let paragraph: string[] = [];
  let listMode: ListMode | null = null;
  let listItems: string[] = [];

  function flushParagraph() {
    if (!paragraph.length) return;
    blocks.push({ type: "paragraph", text: paragraph.join("\n").trim() });
    paragraph = [];
  }

  function flushList() {
    if (!listMode || !listItems.length) return;
    blocks.push({ type: "list", mode: listMode, items: listItems });
    listMode = null;
    listItems = [];
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) {
      flushParagraph();
      flushList();
      blocks.push({ type: "heading", level: heading[1].length as 1 | 2 | 3, text: heading[2].trim() });
      continue;
    }

    const unordered = /^[-*]\s+(.+)$/.exec(line);
    if (unordered) {
      flushParagraph();
      if (listMode !== "ul") flushList();
      listMode = "ul";
      listItems.push(unordered[1].trim());
      continue;
    }

    const ordered = /^\d+\.\s+(.+)$/.exec(line);
    if (ordered) {
      flushParagraph();
      if (listMode !== "ol") flushList();
      listMode = "ol";
      listItems.push(ordered[1].trim());
      continue;
    }

    flushList();
    paragraph.push(line);
  }

  flushParagraph();
  flushList();
  return blocks;
}

function renderHeading(level: 1 | 2 | 3, text: string, key: number) {
  const children = renderInline(text);
  if (level === 1) return <h1 key={key}>{children}</h1>;
  if (level === 2) return <h2 key={key}>{children}</h2>;
  return <h3 key={key}>{children}</h3>;
}

function renderList(mode: ListMode, items: string[], key: number) {
  const children = items.map((item, index) => <li key={`${item}-${index}`}>{renderInline(item)}</li>);
  return mode === "ul" ? <ul key={key}>{children}</ul> : <ol key={key}>{children}</ol>;
}

function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\n)/g).filter((part) => part !== "");

  return parts.map((part, index) => {
    if (part === "\n") return <br key={index} />;

    const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(part);
    if (link && /^https?:\/\//.test(link[2])) {
      return (
        <a key={index} href={link[2]} target="_blank" rel="noreferrer">
          {link[1]}
        </a>
      );
    }

    if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (/^\*[^*]+\*$/.test(part)) return <em key={index}>{part.slice(1, -1)}</em>;
    if (/^`[^`]+`$/.test(part)) return <code key={index}>{part.slice(1, -1)}</code>;
    return part;
  });
}
