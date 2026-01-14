export type SourcePreviewType = 'pdf' | 'audio' | 'video' | 'image' | 'web';

const audioExtensions = ['mp3', 'wav', 'm4a', 'aac', 'flac', 'ogg'];
const videoExtensions = ['mp4', 'mov', 'webm', 'mkv', 'avi'];
const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'];

export const getFileExtension = (value?: string) => {
  if (!value) return '';
  const cleaned = value.split('?')[0]?.split('#')[0] ?? value;
  const match = cleaned.match(/\.([a-z0-9]+)$/i);
  return match ? match[1].toLowerCase() : '';
};

export const getSourcePreviewType = (
  metadata?: Record<string, any>,
): SourcePreviewType => {
  const metadataType = metadata?.type || metadata?.mimeType;
  if (typeof metadataType === 'string') {
    if (metadataType.includes('pdf')) return 'pdf';
    if (metadataType.includes('audio')) return 'audio';
    if (metadataType.includes('video')) return 'video';
    if (metadataType.includes('image')) return 'image';
  }

  const extension =
    getFileExtension(metadata?.url) || getFileExtension(metadata?.title);

  if (extension === 'pdf') return 'pdf';
  if (audioExtensions.includes(extension)) return 'audio';
  if (videoExtensions.includes(extension)) return 'video';
  if (imageExtensions.includes(extension)) return 'image';

  return 'web';
};

export const formatTimestamp = (timestamp?: number) => {
  if (timestamp === undefined || timestamp === null) return undefined;
  const totalSeconds = Math.max(0, Math.floor(timestamp));
  if (Number.isNaN(totalSeconds)) return undefined;
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const pad = (value: number) => value.toString().padStart(2, '0');
  if (hours > 0) {
    return `${hours}:${pad(minutes)}:${pad(seconds)}`;
  }
  return `${pad(minutes)}:${pad(seconds)}`;
};
