import type { AgentFormValues } from "./types";

export type ValidationErrors<T> = Partial<Record<keyof T, string>>;

export function validateAgent(values: AgentFormValues): ValidationErrors<AgentFormValues> {
  const errors: ValidationErrors<AgentFormValues> = {};

  if (!values.name.trim()) errors.name = "Agent name is required.";
  if (!values.targetLanguage.trim()) errors.targetLanguage = "Target language is required.";
  if (values.name.length > 80) errors.name = "Agent name must be 80 characters or fewer.";
  if (values.targetLanguage.length > 80) errors.targetLanguage = "Target language must be 80 characters or fewer.";
  if (values.nativeLanguage.length > 80) errors.nativeLanguage = "Native language must be 80 characters or fewer.";
  if (values.customInstructions.length > 1000) {
    errors.customInstructions = "Custom instructions must be 1,000 characters or fewer.";
  }

  return errors;
}

export async function validateImageFile(file: File): Promise<string> {
  const supported = ["image/png", "image/jpeg", "image/webp", "image/gif"];
  if (!supported.includes(file.type)) return "Upload a PNG, JPEG, WEBP, or non-animated GIF image.";
  if (file.size > 10 * 1024 * 1024) return "Images must be 10 MB or smaller.";
  if (file.type === "image/gif" && (await hasMultipleGifFrames(file))) {
    return "Animated GIFs are not supported. Upload a still PNG, JPEG, WEBP, or non-animated GIF.";
  }
  return "";
}

async function hasMultipleGifFrames(file: File): Promise<boolean> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  if (bytes.length < 13) return false;

  let offset = 13;
  const packed = bytes[10];
  const hasGlobalColorTable = (packed & 0x80) !== 0;
  if (hasGlobalColorTable) {
    const tableSize = 3 * 2 ** ((packed & 0x07) + 1);
    offset += tableSize;
  }

  let frameCount = 0;

  while (offset < bytes.length) {
    const block = bytes[offset++];
    if (block === 0x2c) {
      frameCount += 1;
      if (frameCount > 1) return true;
      offset += 9;
      const localPacked = bytes[offset - 1];
      if ((localPacked & 0x80) !== 0) {
        offset += 3 * 2 ** ((localPacked & 0x07) + 1);
      }
      offset += 1;
      offset = skipGifSubBlocks(bytes, offset);
    } else if (block === 0x21) {
      offset += 1;
      offset = skipGifSubBlocks(bytes, offset);
    } else if (block === 0x3b) {
      break;
    } else {
      break;
    }
  }

  return false;
}

function skipGifSubBlocks(bytes: Uint8Array, offset: number): number {
  while (offset < bytes.length) {
    const blockSize = bytes[offset++];
    if (blockSize === 0) break;
    offset += blockSize;
  }
  return offset;
}

export function validateChatDraft(content: string): string {
  if (!content.trim()) return "Enter a follow-up question.";
  if (content.length > 1000) return "Follow-up questions must be 1,000 characters or fewer.";
  return "";
}
