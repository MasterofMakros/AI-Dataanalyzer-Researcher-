const Citation = ({
  href,
  children,
  'data-title': dataTitle,
  'data-snippet': dataSnippet,
  'data-source-type': dataSourceType,
  'data-file-path': dataFilePath,
  'data-page': dataPage,
  'data-timecode-start': dataTimecodeStart,
  'data-timecode-end': dataTimecodeEnd,
  'data-timestamp': dataTimestamp,
  'data-bbox': dataBbox,
  'data-source-url': dataSourceUrl,
}: {
  href: string;
  children: React.ReactNode;
  'data-title'?: string;
  'data-snippet'?: string;
  'data-source-type'?: string;
  'data-file-path'?: string;
  'data-page'?: string;
  'data-timecode-start'?: string;
  'data-timecode-end'?: string;
  'data-timestamp'?: string;
  'data-bbox'?: string;
  'data-source-url'?: string;
}) => {
  const snippet = dataSnippet?.trim();
  const hasPreview =
    Boolean(snippet) ||
    Boolean(dataTitle) ||
    Boolean(dataFilePath) ||
    Boolean(dataPage) ||
    Boolean(dataTimecodeStart) ||
    Boolean(dataTimecodeEnd);
  const locationParts = [
    dataPage ? `Seite ${dataPage}` : null,
    dataTimecodeStart ? `@ ${dataTimecodeStart}` : null,
    dataTimecodeEnd ? `→ ${dataTimecodeEnd}` : null,
    dataTimestamp ? `t=${dataTimestamp}s` : null,
    dataBbox ? `BBox ${dataBbox}` : null,
  ].filter(Boolean);

  const sourceTypeLabel = dataSourceType ? dataSourceType.toUpperCase() : null;

  return (
    <span className="relative inline-flex group align-baseline">
      <a
        href={href}
        target="_blank"
        className="bg-light-secondary dark:bg-dark-secondary px-1 rounded ml-1 no-underline text-xs text-black/70 dark:text-white/70 relative transition-colors duration-150 group-hover:bg-light-200 dark:group-hover:bg-dark-200"
      >
        {children}
      </a>
      {hasPreview && (
        <span className="pointer-events-none absolute left-0 top-full z-50 mt-2 w-[calc(100vw-2rem)] opacity-0 transition duration-150 group-hover:opacity-100 group-focus-within:opacity-100 sm:left-1/2 sm:w-72 sm:-translate-x-1/2">
          <span className="block rounded-xl border border-light-200/80 bg-light-secondary/95 px-3 py-2 text-xs text-black/80 shadow-xl backdrop-blur dark:border-dark-200/80 dark:bg-dark-secondary/95 dark:text-white/80">
            <span className="flex items-start justify-between gap-2">
              <span className="font-semibold text-black/90 dark:text-white/90 line-clamp-1">
                {dataTitle || dataFilePath || dataSourceUrl}
              </span>
              {sourceTypeLabel && (
                <span className="rounded-full border border-blue-400/40 bg-blue-500/10 px-2 py-0.5 text-[10px] text-blue-500 dark:text-blue-300">
                  {sourceTypeLabel}
                </span>
              )}
            </span>
            {locationParts.length > 0 && (
              <span className="mt-1 block text-[11px] text-black/60 dark:text-white/60">
                {locationParts.join(' ')}
              </span>
            )}
            {snippet && (
              <span className="mt-2 block rounded-md bg-black/5 px-2 py-1 text-[11px] italic text-black/70 dark:bg-white/5 dark:text-white/70">
                “{snippet}”
              </span>
            )}
            {dataFilePath && (
              <span className="mt-2 block text-[10px] text-black/40 dark:text-white/40 line-clamp-1">
                {dataFilePath}
              </span>
            )}
          </span>
        </span>
      )}
    </span>
  );
};

export default Citation;
