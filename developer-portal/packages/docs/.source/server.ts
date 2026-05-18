// @ts-nocheck
import * as __fd_glob_8 from "../content/docs/rate-limits.mdx?collection=docs"
import * as __fd_glob_7 from "../content/docs/onboarding.mdx?collection=docs"
import * as __fd_glob_6 from "../content/docs/index.mdx?collection=docs"
import * as __fd_glob_5 from "../content/docs/data-schema.mdx?collection=docs"
import * as __fd_glob_4 from "../content/docs/cli.mdx?collection=docs"
import * as __fd_glob_3 from "../content/docs/billing.mdx?collection=docs"
import * as __fd_glob_2 from "../content/docs/authentication.mdx?collection=docs"
import * as __fd_glob_1 from "../content/docs/api-reference.mdx?collection=docs"
import { default as __fd_glob_0 } from "../content/docs/meta.json?collection=docs"
import { server } from 'fumadocs-mdx/runtime/server';
import type * as Config from '../source.config';

const create = server<typeof Config, import("fumadocs-mdx/runtime/types").InternalTypeConfig & {
  DocData: {
  }
}>({"doc":{"passthroughs":["extractedReferences"]}});

export const docs = await create.docs("docs", "content/docs", {"meta.json": __fd_glob_0, }, {"api-reference.mdx": __fd_glob_1, "authentication.mdx": __fd_glob_2, "billing.mdx": __fd_glob_3, "cli.mdx": __fd_glob_4, "data-schema.mdx": __fd_glob_5, "index.mdx": __fd_glob_6, "onboarding.mdx": __fd_glob_7, "rate-limits.mdx": __fd_glob_8, });