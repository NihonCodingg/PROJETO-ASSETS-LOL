import { expect, it } from "vitest";

import { SCHEMA_VERSION } from "./index";

it("expõe a versão do contrato", () => {
  expect(SCHEMA_VERSION).toBeTruthy();
});
