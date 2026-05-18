type MarkdownProps = {
  text: string;
};

function formatInline(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

export function Markdown({ text }: MarkdownProps) {
  const lines = text.split('\n');
  const blocks = lines.map((line, index) => {
    if (!line.trim()) {
      return <div className="markdown-space" key={index} />;
    }
    if (line.startsWith('## ')) {
      return (
        <h2 key={index} dangerouslySetInnerHTML={{ __html: formatInline(line.slice(3)) }} />
      );
    }
    if (line.startsWith('### ')) {
      return (
        <h3 key={index} dangerouslySetInnerHTML={{ __html: formatInline(line.slice(4)) }} />
      );
    }
    if (line.startsWith('- ')) {
      return (
        <p className="list-line" key={index} dangerouslySetInnerHTML={{ __html: formatInline(line) }} />
      );
    }
    if (/^\d+\.\s/.test(line)) {
      return (
        <p className="list-line" key={index} dangerouslySetInnerHTML={{ __html: formatInline(line) }} />
      );
    }
    return <p key={index} dangerouslySetInnerHTML={{ __html: formatInline(line) }} />;
  });

  return <div className="markdown">{blocks}</div>;
}
