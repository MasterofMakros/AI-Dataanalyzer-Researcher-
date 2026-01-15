/**
 * Format Icon Component
 * 
 * Maps file formats to appropriate icons for the Research Progress visualization.
 * Uses lucide-react icons with category-based fallbacks.
 */

'use client';

import {
    FileText,
    FileCode,
    FileImage,
    FileAudio,
    FileVideo,
    Mail,
    Archive,
    FileSpreadsheet,
    Presentation,
    Code,
    Database,
    Film,
    FileJson,
    FileType,
    Subtitles,
    Music,
    Image,
    Video,
    File,
    BookOpen,
    type LucideIcon,
} from 'lucide-react';

// Format to icon mapping with specific icons where available
const FORMAT_ICONS: Record<string, LucideIcon> = {
    // Documents
    pdf: FileText,
    doc: FileText,
    docx: FileText,
    odt: FileText,
    rtf: FileText,
    txt: FileText,
    md: FileText,

    // Spreadsheets
    xls: FileSpreadsheet,
    xlsx: FileSpreadsheet,
    ods: FileSpreadsheet,
    csv: FileSpreadsheet,

    // Presentations
    ppt: Presentation,
    pptx: Presentation,
    odp: Presentation,

    // Code
    py: FileCode,
    js: FileCode,
    ts: FileCode,
    java: FileCode,
    c: FileCode,
    cpp: FileCode,
    go: FileCode,
    rs: FileCode,
    rb: FileCode,
    php: FileCode,
    swift: FileCode,
    kt: FileCode,
    scala: FileCode,
    r: FileCode,
    pl: FileCode,
    hs: FileCode,
    ex: FileCode,
    dart: FileCode,
    vue: FileCode,
    scss: FileCode,
    css: FileCode,
    sh: Code,
    ps1: Code,
    sql: Database,

    // Config
    yaml: FileJson,
    yml: FileJson,
    toml: FileJson,
    json: FileJson,
    xml: FileJson,
    html: FileJson,
    ini: FileJson,
    conf: FileJson,

    // Subtitles
    srt: Subtitles,
    vtt: Subtitles,
    sub: Subtitles,

    // Images
    jpg: FileImage,
    jpeg: FileImage,
    png: FileImage,
    gif: FileImage,
    bmp: FileImage,
    tiff: FileImage,
    webp: FileImage,
    heic: FileImage,
    svg: Image,
    ico: Image,
    psd: Image,
    raw: Image,

    // Audio
    mp3: FileAudio,
    wav: FileAudio,
    flac: FileAudio,
    ogg: FileAudio,
    m4a: FileAudio,
    aac: FileAudio,
    opus: FileAudio,
    aiff: FileAudio,
    wma: Music,
    mid: Music,
    midi: Music,

    // Video
    mp4: FileVideo,
    mkv: FileVideo,
    avi: FileVideo,
    mov: FileVideo,
    webm: FileVideo,
    flv: FileVideo,
    wmv: Film,
    mpg: Film,
    mpeg: Film,
    m4v: Film,

    // Email
    eml: Mail,
    msg: Mail,

    // Archive
    zip: Archive,
    rar: Archive,
    '7z': Archive,
    tar: Archive,
    gz: Archive,

    // LaTeX/Academic
    tex: BookOpen,
    rst: BookOpen,
    bib: BookOpen,
    log: FileType,
    diff: FileType,
    patch: FileType,

    // Ebooks
    epub: BookOpen,
    mobi: BookOpen,
    azw: BookOpen,
    azw3: BookOpen,
};

// Category-based colors
const FORMAT_COLORS: Record<string, string> = {
    pdf: 'text-red-500',
    docx: 'text-blue-500',
    xlsx: 'text-green-500',
    pptx: 'text-orange-500',
    // Code
    py: 'text-yellow-500',
    js: 'text-yellow-400',
    ts: 'text-blue-400',
    java: 'text-red-400',
    go: 'text-cyan-400',
    rs: 'text-orange-400',
    // Images
    jpg: 'text-purple-400',
    png: 'text-purple-500',
    // Audio
    mp3: 'text-pink-500',
    wav: 'text-pink-400',
    // Video
    mp4: 'text-red-500',
    mkv: 'text-red-400',
    // Archives
    zip: 'text-amber-500',
};

// Category fallbacks
const CATEGORY_ICONS: Record<string, LucideIcon> = {
    documents: FileText,
    code: FileCode,
    config: FileJson,
    subtitles: Subtitles,
    images: FileImage,
    audio: FileAudio,
    video: FileVideo,
    email: Mail,
    archive: Archive,
    latex: BookOpen,
    ebook: BookOpen,
    binary: File,
    app: File,
};

interface FormatIconProps {
    format: string;
    size?: number;
    className?: string;
}

const FormatIcon = ({ format, size = 16, className = '' }: FormatIconProps) => {
    const normalizedFormat = format.toLowerCase().replace('.', '');
    const Icon = FORMAT_ICONS[normalizedFormat] || File;
    const colorClass = FORMAT_COLORS[normalizedFormat] || 'text-gray-400';

    return (
        <Icon
            size={size}
            className={`${colorClass} ${className}`}
            data-testid="format-icon"
        />
    );
};

// Get category for a format
export const getFormatCategory = (format: string): string => {
    const f = format.toLowerCase();

    const categoryMap: Record<string, string[]> = {
        documents: ['pdf', 'doc', 'docx', 'odt', 'rtf', 'txt', 'md', 'xls', 'xlsx', 'ods', 'csv', 'ppt', 'pptx', 'odp'],
        code: ['py', 'js', 'ts', 'java', 'c', 'cpp', 'go', 'rs', 'rb', 'php', 'swift', 'kt', 'scala', 'r', 'pl', 'hs', 'ex', 'dart', 'vue', 'scss', 'css', 'sh', 'ps1', 'sql'],
        config: ['yaml', 'yml', 'toml', 'json', 'xml', 'html', 'ini', 'conf'],
        subtitles: ['srt', 'vtt', 'sub'],
        images: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'heic', 'svg', 'ico', 'psd', 'raw'],
        audio: ['mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac', 'opus', 'aiff', 'wma', 'mid', 'midi'],
        video: ['mp4', 'mkv', 'avi', 'mov', 'webm', 'flv', 'wmv', 'mpg', 'mpeg', 'm4v'],
        email: ['eml', 'msg'],
        archive: ['zip', 'rar', '7z', 'tar', 'gz'],
        latex: ['tex', 'rst', 'bib', 'log', 'diff', 'patch'],
        ebook: ['epub', 'mobi', 'azw', 'azw3'],
    };

    for (const [category, formats] of Object.entries(categoryMap)) {
        if (formats.includes(f)) return category;
    }
    return 'unknown';
};

// Get icon for a category
export const getCategoryIcon = (category: string): LucideIcon => {
    return CATEGORY_ICONS[category] || File;
};

export default FormatIcon;
