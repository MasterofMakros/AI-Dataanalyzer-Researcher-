'use client';

import { Claim, Chunk } from '@/lib/types';
import { BadgeCheck, AlertTriangle } from 'lucide-react';

const ClaimsList = ({
  claims,
  sources,
}: {
  claims: Claim[];
  sources: Chunk[];
}) => {
  if (claims.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex flex-row items-center space-x-2">
        <BadgeCheck className="text-black dark:text-white" size={20} />
        <h3 className="text-black dark:text-white font-medium text-xl">
          Claims
        </h3>
      </div>
      <div className="flex flex-col space-y-3">
        {claims.map((claim) => {
          const evidenceIds = Array.from(
            new Set(
              claim.evidenceIds.filter(
                (id) => id > 0 && id <= sources.length,
              ),
            ),
          );
          const isVerified = claim.verified && evidenceIds.length > 0;

          return (
            <div
              key={claim.id}
              className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-3 flex flex-col space-y-2"
            >
              <p className="text-sm text-black dark:text-white leading-relaxed">
                {claim.text}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                {evidenceIds.map((id) => {
                  const source = sources[id - 1];
                  const url = source?.metadata?.url;
                  const label = source?.metadata?.title || url || `Source ${id}`;
                  const badgeClass =
                    'text-xs px-2 py-1 rounded-full border border-light-200 dark:border-dark-200 bg-light-200/60 dark:bg-dark-200/60 text-black/70 dark:text-white/70 hover:text-black dark:hover:text-white transition';
                  const anchor = `#evidence-${id}`;

                  return (
                    <a
                      key={id}
                      href={anchor}
                      className={badgeClass}
                      title={label}
                    >
                      Source {id}
                    </a>
                  );
                })}
                {!isVerified && (
                  <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full border border-amber-200 dark:border-amber-500/40 bg-amber-100/70 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300">
                    <AlertTriangle size={12} />
                    Unverified
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ClaimsList;
