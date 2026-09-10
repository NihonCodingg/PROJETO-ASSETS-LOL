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

import { useCallback, useEffect, useMemo, useState } from "react";

import type { Asset, AssetCategory, IndexShard } from "@lol-assets/schema";

import { BarraDeLote } from "@/components/barra-de-lote";
import { PainelDeAsset } from "@/components/painel-de-asset";
import { Botao } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import {
  descreverFiltro,
  filtrar,
  filtrosPadrao,
  gruposDeFiltro,
  prepararLista,
  rotuloDaCategoria,
} from "@/lib/categorias";
import { alternar, selecionados, tudoDo } from "@/lib/selecao";
import { cn } from "@/lib/utils";

export interface NavegacaoPorCategoriaProps {
  /**
   * A categoria aberta, decidida de fora.
   *
   * Os botões moram na barra lateral desde o **T-41**; este componente virou o
   * conteúdo. Antes ele era dono dos dois, e a lista de categorias acabava
   * embaixo de 173 cartões de campeão — para chegar em "Itens" era preciso
   * rolar a grade inteira.
   */
  readonly aberta: AssetCategory | null;
  readonly carregar: (category: AssetCategory) => Promise<IndexShard>;
  /** Fecha a categoria e volta para a grade de campeões. */
  readonly onFechar: () => void;
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
  aberta,
  carregar,
  onFechar,
  assetsBaseUrl,
}: NavegacaoPorCategoriaProps) {
  const [carga, setCarga] = useState<Carga>({ fase: "vazia" });
  const [marcadas, setMarcadas] = useState<ReadonlySet<string>>(new Set());
  const [consulta, setConsulta] = useState("");
  const [selecao, setSelecao] = useState<ReadonlySet<string>>(new Set());

  /**
   * Carrega a fatia quando a categoria aberta muda.
   *
   * Efeito, e não manipulador de clique, porque quem clica agora é a barra
   * lateral: este componente descobre a mudança pela prop. O `cancelado` é o
   * de sempre — trocar de categoria duas vezes rápido não pode deixar a
   * resposta da primeira sobrescrever a da segunda.
   */
  useEffect(() => {
    if (aberta === null) {
      setCarga({ fase: "vazia" });
      return;
    }

    let cancelado = false;
    setConsulta("");
    setMarcadas(new Set());
    setSelecao(new Set());
    setCarga({ fase: "carregando" });

    (async () => {
      try {
        const shard = await carregar(aberta);
        if (cancelado) return;
        // O filtro padrão depende das etiquetas que a fatia traz (§B.1.6 do
        // KICKOFF), então só dá para calculá-lo depois de ela chegar.
        setMarcadas(filtrosPadrao(aberta, gruposDeFiltro(shard.assets)));
        setCarga({ fase: "pronta", assets: shard.assets });
      } catch (erro) {
        if (cancelado) return;
        setCarga({ fase: "erro", motivo: erro instanceof Error ? erro.message : String(erro) });
      }
    })();

    return () => {
      cancelado = true;
    };
  }, [aberta, carregar]);

  const assets = carga.fase === "pronta" ? carga.assets : SEM_ASSETS;
  const grupos = useMemo(() => gruposDeFiltro(assets), [assets]);
  const lista = useMemo(() => prepararLista(assets), [assets]);
  const filtrados = useMemo(() => filtrar(lista, marcadas, consulta), [lista, marcadas, consulta]);
  // O lote alcança o que o filtro deixou na tela — nunca a fatia inteira por
  // baixo dele. "Selecionar todos" com 5.042 escondidos seria uma armadilha.
  const noLote = useMemo(() => selecionados(filtrados, selecao), [filtrados, selecao]);

  const alternarFiltro = useCallback((tag: string) => {
    setMarcadas((antes) => {
      const proximo = new Set(antes);
      if (!proximo.delete(tag)) proximo.add(tag);
      return proximo;
    });
  }, []);

  return (
    <section aria-label="Categorias" className="flex min-h-0 flex-1 flex-col">
      {aberta && (
        <div className="flex h-barra flex-none items-center gap-2.5 border-b border-borda bg-fundo-barra px-3.5">
          <span className="text-12 font-medium text-texto-forte">{rotuloDaCategoria(aberta)}</span>
          <Botao variante="fantasma" tamanho="md" className="ml-auto" onClick={onFechar}>
            voltar aos campeões
          </Botao>
        </div>
      )}

      {aberta && carga.fase === "carregando" && (
        <p className="px-3.5 py-3 text-13 text-texto-suave">
          carregando {rotuloDaCategoria(aberta)}…
        </p>
      )}
      {aberta && carga.fase === "erro" && (
        <p role="alert" className="px-3.5 py-3 text-13 text-acento-mais-claro">
          Falhou ao carregar: {carga.motivo}
        </p>
      )}

      {aberta && carga.fase === "pronta" && (
        <section
          aria-label={`Filtros de ${rotuloDaCategoria(aberta)}`}
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="flex flex-none flex-wrap items-center gap-2.5 border-y border-borda bg-fundo-barra px-3.5 py-2">
            <label className="flex items-center gap-2 font-mono text-10 uppercase tracking-rotulo text-texto-suave">
              Filtrar por texto
              <Campo
                type="search"
                value={consulta}
                onChange={(evento) => setConsulta(evento.target.value)}
                className="w-44 normal-case tracking-normal"
              />
            </label>

            {grupos.map((grupo) => (
              <fieldset key={grupo.chave} className="flex flex-wrap items-center gap-1">
                <legend className="float-left mr-2 font-mono text-10 uppercase tracking-rotulo text-texto-suave">
                  {grupo.rotulo}
                </legend>
                {grupo.opcoes.map((opcao) => (
                  <label
                    key={opcao.tag}
                    className={cn(
                      "cursor-pointer rounded-padrao border px-1.75 py-0.75 text-11",
                      marcadas.has(opcao.tag)
                        ? "border-acento bg-acento-suave text-texto"
                        : "border-borda-forte text-texto-suave hover:bg-campo hover:text-texto",
                    )}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={marcadas.has(opcao.tag)}
                      onChange={() => alternarFiltro(opcao.tag)}
                    />
                    {opcao.rotulo} ({opcao.total})
                  </label>
                ))}
              </fieldset>
            ))}

            {/* §B.1.6: a categoria `item` abre filtrada, e isto é a saída. */}
            {marcadas.size > 0 && (
              <Botao variante="fantasma" tamanho="md" onClick={() => setMarcadas(new Set())}>
                Mostrar tudo
              </Botao>
            )}

            <p className="ml-auto font-mono text-11 text-texto-suave">
              {filtrados.length} de {assets.length}
            </p>
          </div>

          {filtrados.length === 0 ? (
            <Vazio descricao={descreverFiltro(marcadas, consulta, grupos)} />
          ) : (
            <>
              <Botao
                tamanho="md"
                className="m-3.5 flex-none self-start"
                onClick={() => setSelecao(tudoDo(filtrados, true))}
              >
                Selecionar os {filtrados.length} filtrados
              </Botao>

              <BarraDeLote
                assets={noLote}
                rotulo={rotuloDaCategoria(aberta)}
                assetsBaseUrl={assetsBaseUrl}
                onLimpar={() => setSelecao(new Set())}
              />

              <PainelDeAsset
                titulo={rotuloDaCategoria(aberta)}
                assets={filtrados}
                assetsBaseUrl={assetsBaseUrl}
                onClose={onFechar}
                selecao={selecao}
                onAlternar={(id) => setSelecao((antes) => alternar(antes, id))}
              />
            </>
          )}
        </section>
      )}
    </section>
  );
}

/** Critério 4: o vazio diz **o que** foi filtrado, não só que deu zero. */
function Vazio({ descricao }: { descricao: readonly string[] }) {
  return (
    <div role="status" className="px-3.5 py-20 text-center">
      <p className="mb-1 text-14 font-medium">Nenhum asset com esse filtro.</p>
      {descricao.length > 0 && (
        <ul
          aria-label="Filtro aplicado"
          className="flex flex-wrap justify-center gap-1.5 font-mono text-11 text-texto-suave"
        >
          {descricao.map((parte) => (
            <li key={parte} className="rounded-padrao border border-borda-forte px-2 py-0.75">
              {parte}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
