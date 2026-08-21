import type { HbarBucket } from './HbarVisual'
import type { Topic } from './TopicCardGrid'

export const ACTS = [
  { key: 'opening', label: 'Opening' },
  { key: 'conflict', label: 'Conflict' },
  { key: 'climax', label: 'Climax' },
] as const

export function buildActBuckets(topics: Topic[]): { buckets: HbarBucket[]; extraBucket: HbarBucket } {
  const buckets: HbarBucket[] = ACTS.map((act) => {
    const bucketTopics = topics.filter((t) => t.act === act.key)
    return {
      key: act.key,
      label: act.label,
      topics: bucketTopics,
      activeTopics: bucketTopics.filter((t) => !t.excluded),
    }
  })
  const unassignedTopics = topics.filter((t) => t.act === null)
  const extraBucket: HbarBucket = {
    key: 'unassigned',
    label: 'Unassigned',
    topics: unassignedTopics,
    activeTopics: unassignedTopics.filter((t) => !t.excluded),
  }
  return { buckets, extraBucket }
}
