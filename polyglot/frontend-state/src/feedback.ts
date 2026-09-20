(() => {
  'use strict';

  type FeedbackKind =
    | 'correction' | 'evidence_correction' | 'preference' | 'task_success'
    | 'task_failure' | 'ui' | 'disagreement' | 'rating' | 'behavioral';

  interface FeedbackInput {
    runId?: string | null;
    messageId?: string | null;
    kind: FeedbackKind;
    rating?: number | null;
    receiptIds?: readonly string[];
  }

  interface FeedbackRecord {
    schema_version: 'chat-feedback/v1';
    created_at: string;
    run_id: string | null;
    message_id: string | null;
    kind: FeedbackKind;
    rating: number | null;
    receipt_ids: readonly string[];
    authority: 'candidate';
    evidence_overwrite_allowed: false;
  }

  const ALLOWED = new Set<FeedbackKind>([
    'correction', 'evidence_correction', 'preference', 'task_success',
    'task_failure', 'ui', 'disagreement', 'rating', 'behavioral',
  ]);

  function createFeedback({
    runId = null,
    messageId = null,
    kind,
    rating = null,
    receiptIds = [],
  }: FeedbackInput): FeedbackRecord {
    if (!ALLOWED.has(kind)) throw new Error(`unsupported feedback kind: ${kind}`);
    if (!Array.isArray(receiptIds) || receiptIds.length > 64) throw new Error('receiptIds exceeds limit');
    if (rating !== null && (!Number.isInteger(rating) || rating < 1 || rating > 5)) {
      throw new Error('rating must be an integer from 1 to 5');
    }
    return Object.freeze({
      schema_version: 'chat-feedback/v1',
      created_at: new Date().toISOString(),
      run_id: runId,
      message_id: messageId,
      kind,
      rating,
      receipt_ids: Object.freeze([...receiptIds]),
      authority: 'candidate',
      evidence_overwrite_allowed: false,
    });
  }

  const target = window as Window & { RIEFeedback?: Record<string, unknown> };
  target.RIEFeedback = Object.freeze({
    createFeedback,
    allowedKinds: Object.freeze([...ALLOWED]),
  });
})();