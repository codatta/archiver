// @ts-nocheck
import { browser } from 'fumadocs-mdx/runtime/browser';
import type * as Config from '../source.config';

const create = browser<typeof Config, import("fumadocs-mdx/runtime/types").InternalTypeConfig & {
  DocData: {
  }
}>();
const browserCollections = {
  docs: create.doc("docs", {"api-reference.mdx": () => import("../content/docs/api-reference.mdx?collection=docs"), "authentication.mdx": () => import("../content/docs/authentication.mdx?collection=docs"), "billing.mdx": () => import("../content/docs/billing.mdx?collection=docs"), "cli.mdx": () => import("../content/docs/cli.mdx?collection=docs"), "data-schema.mdx": () => import("../content/docs/data-schema.mdx?collection=docs"), "index.mdx": () => import("../content/docs/index.mdx?collection=docs"), "onboarding.mdx": () => import("../content/docs/onboarding.mdx?collection=docs"), "rate-limits.mdx": () => import("../content/docs/rate-limits.mdx?collection=docs"), }),
};
export default browserCollections;