import styles from "./MarkdownLesson.module.css";

type MarkdownLessonProps = {
  markdown: string;
};

export default function MarkdownLesson({ markdown }: MarkdownLessonProps) {
  const blocks = markdown.split(/\n{2,}/).map((block) => block.trim()).filter(Boolean);

  return (
    <article className={styles.lesson}>
      {blocks.map((block, index) => renderBlock(block, index))}
    </article>
  );
}

function renderBlock(block: string, index: number) {
  if (block.startsWith("### ")) return <h3 key={index}>{block.slice(4)}</h3>;
  if (block.startsWith("## ")) return <h2 key={index}>{block.slice(3)}</h2>;
  if (block.startsWith("# ")) return <h1 key={index}>{block.slice(2)}</h1>;

  const lines = block.split("\n");
  if (lines.every((line) => /^[-*]\s+/.test(line))) {
    return (
      <ul key={index}>
        {lines.map((line) => (
          <li key={line}>{line.replace(/^[-*]\s+/, "")}</li>
        ))}
      </ul>
    );
  }

  if (lines.every((line) => /^\d+\.\s+/.test(line))) {
    return (
      <ol key={index}>
        {lines.map((line) => (
          <li key={line}>{line.replace(/^\d+\.\s+/, "")}</li>
        ))}
      </ol>
    );
  }

  return <p key={index}>{lines.join(" ")}</p>;
}
