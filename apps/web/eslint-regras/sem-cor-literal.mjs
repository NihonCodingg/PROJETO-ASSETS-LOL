/**
 * Critério 2 do T-34: nenhuma cor literal fora do tema.
 *
 * O que esta regra protege é específico: uma cor escrita à mão num componente
 * não aparece no `TOKENS.md`, não entra no teste de paridade e não muda quando o
 * design mudar. Ela vira uma segunda fonte de verdade — e a segunda fonte de
 * verdade sempre ganha por acidente.
 *
 * Pega os dois jeitos de escrever cor num componente:
 *
 *     style={{ color: "#8b5cf6" }}      // literal em objeto de estilo
 *     className="bg-[#8b5cf6]"          // valor arbitrário do Tailwind
 *
 * **Escopo: só cor.** Espaçamento e raio arbitrários (`px-[10px]`) ficam de fora
 * porque o Tailwind v4 já cobre a escala inteira com `px-2.5`, e uma regra que
 * também os proibisse pegaria `top-[3px]` de posicionamento — ruído sem ganho.
 * O que quebra um sistema de design duplicado é a cor. A restrição do escopo
 * está registrada no ticket.
 */
const COR = /#[0-9a-fA-F]{3,8}\b|\brgba?\s*\(/;

/**
 * Onde cor literal é o certo.
 *
 * O tema é a origem, e os testes precisam escrever a cor que estão verificando.
 */
const PERMITIDOS = [/globals\.css$/, /\.test\.tsx?$/, /eslint-regras[\\/]/];

const regra = {
  meta: {
    type: "problem",
    docs: { description: "Cor literal fora do tema (T-34, critério 2)." },
    schema: [],
    messages: {
      literal:
        "Cor literal '{{ cor }}' fora do tema. Use um token de docs/design/TOKENS.md — " +
        "cor escrita à mão não entra no teste de paridade nem muda quando o design mudar.",
    },
  },
  create(context) {
    const arquivo = context.filename ?? context.getFilename();
    if (PERMITIDOS.some((padrao) => padrao.test(arquivo))) return {};

    function conferir(no, texto) {
      const achado = COR.exec(texto);
      if (achado) context.report({ node: no, messageId: "literal", data: { cor: achado[0] } });
    }

    return {
      Literal(no) {
        if (typeof no.value === "string") conferir(no, no.value);
      },
      TemplateElement(no) {
        conferir(no, no.value.raw);
      },
    };
  },
};

export default regra;
