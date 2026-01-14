import React from 'react';
import { ClaimItem } from '@/lib/types';

const ClaimBadges = ({ claims }: { claims: ClaimItem[] }) => {
  if (claims.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-black dark:text-white font-medium text-xl">
          Claims
        </span>
      </div>
      <div className="flex flex-col space-y-3">
        {claims.map((claim) => (
          <div
            key={claim.id}
            className="rounded-xl border border-light-200 dark:border-dark-200 bg-light-secondary/60 dark:bg-dark-secondary/60 p-4 space-y-2"
          >
            <p className="text-sm text-black/80 dark:text-white/80">
              {claim.text}
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold ${
                  claim.verified
                    ? 'border border-emerald-400/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                    : 'border border-amber-400/40 bg-amber-500/10 text-amber-600 dark:text-amber-300'
                }`}
              >
                {claim.verified ? 'Verifiziert' : 'Unverifiziert'}
              </span>
              {claim.evidence.length > 0 ? (
                claim.evidence.map((evidence) =>
                  evidence.url ? (
                    <a
                      key={evidence.id}
                      href={evidence.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 rounded-full border border-blue-400/40 bg-blue-500/10 px-2.5 py-1 text-[11px] text-blue-600 dark:text-blue-300 hover:bg-blue-500/20 transition"
                    >
                      <span className="font-semibold">{evidence.id}</span>
                      <span className="line-clamp-1 max-w-[180px]">
                        {evidence.title ?? 'Quelle'}
                      </span>
                    </a>
                  ) : (
                    <span
                      key={evidence.id}
                      className="inline-flex items-center gap-1 rounded-full border border-blue-400/40 bg-blue-500/10 px-2.5 py-1 text-[11px] text-blue-600 dark:text-blue-300"
                    >
                      <span className="font-semibold">{evidence.id}</span>
                      <span className="line-clamp-1 max-w-[180px]">
                        {evidence.title ?? 'Quelle'}
                      </span>
                    </span>
                  ),
                )
              ) : (
                <span className="text-[11px] text-black/50 dark:text-white/50">
                  Keine Evidenzquellen gefunden.
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ClaimBadges;
