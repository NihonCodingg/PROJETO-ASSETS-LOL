"use client";

/**
 * Navegação por categoria (RF-08) — o caminho de quem não sabe o nome.
 *
 * A home é a busca e a grade de campeões ([ADR 0010]). Isto é o outro caminho:
 * escolher uma categoria e ir reduzindo. Quem quer "um ícone de bota" não tem
 * termo para digitar, e é essa pessoa que este componente atende.
 *
 * **Nada é carregado antes do clique.** A fatia entra sob demanda, memoizada
 * pelo `AssetsClient` — abrir Itens, sair e voltar não busca de novo. Enquanto
 * ninguém abre categoria nenhuma, a home segue com manifesto e catálogo, que é
 * a promessa do RNF-03.
 *
 * Os filtros saem das `tags` que o T-21 escreveu no índice, e **só delas**: a
 * lista de grupos é derivada da fatia carregada, não declarada aqui. Ver
 * `lib/categorias.ts` para o porquê de cada rótulo.
 *
 * Tela crua de propósito; o design chega no T-30.
 */

import { useCallback, useMemo, useState } from "react";

import type { Asset, AssetCategory, IndexShard } from "@lol-assets/schema";

import { PainelDeAsset } from "@/components/painel-de-asset";
import {
  categoriasDisponiveis,
  descreverFiltro,
  filtrar,
  filtrosPadrao,
  gruposDeFiltro,
  prepararLista,
  rotuloDaCategoria,
} from "@/lib/categorias";

export interface NavegacaoPorCategoriaProps {
  /** As fatias que o manifesto declara. Categoria fora daqui não vira botão. */
  readonly shards: readonly { category: string }[];
  readonly carregar: (category: AssetCategory) => Promise<IndexShard>;
  readonly assetsBaseUrl?: string;
}

/** Referência estável: sem ela, todo `useMemo` a jusante recalcula por render. */
const SEM_ASSETS: readonly Asset[] = [];

type Carga =
  | { fase: "vazia" }
  | { fase: "carregando" }
  | { fase: "erro"; motivo: string }
  | { fase: "pronta"; assets: readonly Asset[] };

export function NavegacaoPorCategoria({
  shards,
  carregar,
  assetsBaseUrl,
}: NavegacaoPorCategoriaProps) {
  const categorias = useMemo(() => categoriasDisponiveis(shards), [shards]);
  const [aberta, setAberta] = useState<AssetCategory | null>(null);
  const [carga, setCarga] = useState<Carga>({ fase: "vazia" });
  const [marcadas, setMarcadas] = useState<ReadonlySet<string>>(new Set());
  const [consulta, setConsulta] = useState("");

  const abrir = useCallback(
    async (category: AssetCategory) => {
      setAberta(category);
      setConsulta("");
      setMarcadas(new Set());
      setCarga({ fase: "carregando" });
      try {
        const shard = await carregar(category);
        // O filtro padrão depende das etiquetas que a fatia traz (§B.1.6 do
        // KICKOFF), então só dá para calculá-lo aqui — e aqui, não num efeito
        // depois do render: efeito que reage à chegada da fatia corre com o
        // clique do usuário, e quem perde a corrida é o clique.
        setMarcadas(filtrosPadrao(category, gruposDeFiltro(shard.assets)));
        setCarga({ fase: "pronta", assets: shard.assets });
      } catch (erro) {
        setCarga({ fase: "erro", motivo: erro instanceof Error ? erro.message : String(erro) });
      }
    },
    [carregar],
  );

  const assets = carga.fase === "pronta" ? carga.assets : SEM_ASSETS;
  const grupos = useMemo(() => gruposDeFiltro(assets), [assets]);
  const lista = useMemo(() => prepararLista(assets), [assets]);
  const filtrados = useMemo(() => filtrar(lista, marcadas, consulta), [lista, marcadas, consulta]);

  const alternar = useCallback((tag: string) => {
    setMarcadas((antes) => {
      const proximo = new Set(antes);
      if (!proximo.delete(tag)) proximo.add(tag);
      return proximo;
    });
  }, []);

  return (
    <section aria-label="Categorias">
      <h2>Categorias</h2>
      <ul>
        {categorias.map((categoria) => (
          <li key={categoria.category}>
            <button
              type="button"
              aria-pressed={aberta === categoria.category}
              onClick={() => void abrir(categoria.category)}
            >
              {categoria.rotulo}
            </button>
          </li>
        ))}
      </ul>

      {aberta && carga.fase === "carregando" && <p>carregando {rotuloDaCategoria(aberta)}…</p>}
      {aberta && carga.fase === "erro" && <p role="alert">Falhou ao carregar: {carga.motivo}</p>}

      {aberta && carga.fase === "pronta" && (
        <section aria-label={`Filtros de ${rotuloDaCategoria(aberta)}`}>
          <label>
            Filtrar por texto
            <input
              type="search"
              value={consulta}
              onChange={(evento) => setConsulta(evento.target.value)}
            />
          </label>

          {grupos.map((grupo) => (
            <fieldset key={grupo.chave}>
              <legend>{grupo.rotulo}</legend>
              {grupo.opcoes.map((opcao) => (
                <label key={opcao.tag}>
                  <input
                    type="checkbox"
                    checked={marcadas.has(opcao.tag)}
                    onChange={() => alternar(opcao.tag)}
                  />
                  {opcao.rotulo} ({opcao.total})
                </label>
              ))}
            </fieldset>
          ))}

          {/* §B.1.6: a categoria `item` abre filtrada, e isto é a saída. */}
          {marcadas.size > 0 && (
            <button type="button" onClick={() => setMarcadas(new Set())}>
              Mostrar tudo
            </button>
          )}

          <p>
            {filtrados.length} de {assets.length}
          </p>

          {filtrados.length === 0 ? (
            <Vazio descricao={descreverFiltro(marcadas, consulta, grupos)} />
          ) : (
            <PainelDeAsset
              titulo={rotuloDaCategoria(aberta)}
              assets={filtrados}
              assetsBaseUrl={assetsBaseUrl}
              onClose={() => setAberta(null)}
            />
          )}
        </section>
      )}
    </section>
  );
}

/** Critério 4: o vazio diz **o que** foi filtrado, não só que deu zero. */
function Vazio({ descricao }: { descricao: readonly string[] }) {
  return (
    <div role="status">
      <p>Nenhum asset com esse filtro.</p>
      {descricao.length > 0 && (
        <ul aria-label="Filtro aplicado">
          {descricao.map((parte) => (
            <li key={parte}>{parte}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
