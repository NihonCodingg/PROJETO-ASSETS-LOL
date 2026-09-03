"use client";

/**
 * Protótipo descartável — valida a regra dos 3 cliques (§A.4 item 2) e o
 * ADR 0001 (bytes originais no CDN, PNG convertido no navegador).
 *
 * Sem back-end, sem testes, sem polimento. Fala direto com o ddragon.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const DDRAGON = "https://ddragon.leagueoflegends.com";

type Champion = { id: string; key: string; name: string; title: string };

/** Nomes canônicos do ADR 0002 — nunca os nomes da fonte. */
const TIPOS = [
  {
    slug: "square",
    rotulo: "Square",
    url: (v: string, c: Champion) => `${DDRAGON}/cdn/${v}/img/champion/${c.id}.png`,
  },
  {
    slug: "splash_centered",
    rotulo: "Splash centralizada (padrão)",
    url: (_v: string, c: Champion) => `${DDRAGON}/cdn/img/champion/centered/${c.id}_0.jpg`,
  },
  {
    slug: "splash_wide",
    rotulo: "Splash aberta",
    url: (_v: string, c: Champion) => `${DDRAGON}/cdn/img/champion/splash/${c.id}_0.jpg`,
  },
  {
    slug: "loading",
    rotulo: "Loading screen",
    url: (_v: string, c: Champion) => `${DDRAGON}/cdn/img/champion/loading/${c.id}_0.jpg`,
  },
] as const;

/**
 * Apelidos que nenhuma fonte fornece (§B.1.5). Aqui só para medir se a busca
 * fica boa o bastante sem uma tabela grande.
 */
const APELIDOS: Record<string, string> = {
  mf: "MissFortune",
  tf: "TwistedFate",
  j4: "JarvanIV",
  asol: "AurelionSol",
  mundo: "DrMundo",
  yi: "MasterYi",
  ww: "Warwick",
  cait: "Caitlyn",
  blitz: "Blitzcrank",
  morde: "Mordekaiser",
  panth: "Pantheon",
  eve: "Evelynn",
  gp: "Gangplank",
  sett: "Sett",
  nunu: "Nunu",
};

function normalizar(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

function bytesLegiveis(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function baixarBlob(blob: Blob, nome: string): void {
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = nome;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(href), 2000);
}

type Medida =
  | { estado: "carregando" }
  | { estado: "erro"; motivo: string }
  | {
      estado: "pronto";
      blob: Blob;
      previa: string;
      largura: number;
      altura: number;
      mime: string;
    };

export default function ProtoPage() {
  const [versao, setVersao] = useState<string | null>(null);
  const [campeoes, setCampeoes] = useState<Champion[]>([]);
  const [erroCatalogo, setErroCatalogo] = useState<string | null>(null);
  const [busca, setBusca] = useState("");
  const [selecionado, setSelecionado] = useState<Champion | null>(null);
  const [medidas, setMedidas] = useState<Record<string, Medida>>({});
  const [copiado, setCopiado] = useState<string | null>(null);
  const campoBusca = useRef<HTMLInputElement>(null);

  // 1. versão mais recente + catálogo em pt_BR
  useEffect(() => {
    let vivo = true;
    (async () => {
      try {
        const versoes: string[] = await (await fetch(`${DDRAGON}/api/versions.json`)).json();
        const atual = versoes[0];
        const payload = await (
          await fetch(`${DDRAGON}/cdn/${atual}/data/pt_BR/champion.json`)
        ).json();
        if (!vivo) return;
        setVersao(atual);
        setCampeoes(
          Object.values(payload.data as Record<string, Champion>).sort((a, b) =>
            a.name.localeCompare(b.name, "pt-BR"),
          ),
        );
      } catch (erro) {
        if (vivo) setErroCatalogo(erro instanceof Error ? erro.message : String(erro));
      }
    })();
    return () => {
      vivo = false;
    };
  }, []);

  // atalho "/" foca a busca (§A.4 item 6)
  useEffect(() => {
    function aoTeclar(evento: KeyboardEvent) {
      if (evento.key === "/" && document.activeElement !== campoBusca.current) {
        evento.preventDefault();
        campoBusca.current?.focus();
      }
      if (evento.key === "Escape") setSelecionado(null);
    }
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, []);

  const resultados = useMemo(() => {
    const alvo = normalizar(busca);
    if (!alvo) return campeoes;
    const porApelido = APELIDOS[alvo];
    return campeoes.filter((c) => {
      if (porApelido && c.id === porApelido) return true;
      return normalizar(c.name).includes(alvo) || normalizar(c.id).includes(alvo);
    });
  }, [busca, campeoes]);

  // 2. ao escolher um campeão, baixa cada asset uma vez e mede de verdade
  const abrir = useCallback(
    (campeao: Champion) => {
      setSelecionado(campeao);
      setMedidas({});
      if (!versao) return;
      for (const tipo of TIPOS) {
        const url = tipo.url(versao, campeao);
        setMedidas((atual) => ({ ...atual, [tipo.slug]: { estado: "carregando" } }));
        (async () => {
          try {
            const resposta = await fetch(url, { mode: "cors" });
            if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
            const blob = await resposta.blob();
            const bitmap = await createImageBitmap(blob);
            // Ler antes de fechar: `close()` zera width/height, e o updater do
            // setState roda depois — foi assim que a ficha veio 0x0 na primeira versão.
            const largura = bitmap.width;
            const altura = bitmap.height;
            bitmap.close();
            setMedidas((atual) => ({
              ...atual,
              [tipo.slug]: {
                estado: "pronto",
                blob,
                previa: URL.createObjectURL(blob),
                largura,
                altura,
                mime: blob.type,
              },
            }));
          } catch (erro) {
            setMedidas((atual) => ({
              ...atual,
              [tipo.slug]: {
                estado: "erro",
                motivo: erro instanceof Error ? erro.message : String(erro),
              },
            }));
          }
        })();
      }
    },
    [versao],
  );

  // 3. conversão para PNG no navegador — o coração do ADR 0001
  const baixarComoPng = useCallback(async (medida: Medida, nomeBase: string) => {
    if (medida.estado !== "pronto") return;
    const bitmap = await createImageBitmap(medida.blob);
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const contexto = canvas.getContext("2d");
    if (!contexto) return;
    contexto.drawImage(bitmap, 0, 0);
    bitmap.close();
    const png = await new Promise<Blob | null>((resolver) =>
      canvas.toBlob(resolver, "image/png"),
    );
    if (png) baixarBlob(png, `${nomeBase}.png`);
  }, []);

  const copiarUrl = useCallback(async (url: string, slug: string) => {
    await navigator.clipboard.writeText(url);
    setCopiado(slug);
    window.setTimeout(() => setCopiado(null), 1500);
  }, []);

  return (
    <main>
      <header className="topo">
        <input
          ref={campoBusca}
          autoFocus
          className="busca"
          placeholder="Buscar campeão…  (atalho: / )"
          value={busca}
          onChange={(evento) => setBusca(evento.target.value)}
        />
        <span className="meta">
          {versao ? `patch ${versao} · ${resultados.length} de ${campeoes.length}` : "carregando…"}
        </span>
      </header>

      {erroCatalogo && <p className="erro">Falhou ao carregar o catálogo: {erroCatalogo}</p>}

      <div className="grade">
        {resultados.map((campeao) => (
          <button key={campeao.id} className="card" onClick={() => abrir(campeao)}>
            {versao && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                src={`${DDRAGON}/cdn/${versao}/img/champion/${campeao.id}.png`}
                alt={campeao.name}
                width={96}
                height={96}
                loading="lazy"
              />
            )}
            <span>{campeao.name}</span>
          </button>
        ))}
      </div>

      {selecionado && versao && (
        <div className="painel" role="dialog" aria-label={selecionado.name}>
          <div className="painel-topo">
            <h2>
              {selecionado.name} <small>{selecionado.title}</small>
            </h2>
            <button className="fechar" onClick={() => setSelecionado(null)}>
              fechar (Esc)
            </button>
          </div>

          {TIPOS.map((tipo) => {
            const url = tipo.url(versao, selecionado);
            const medida = medidas[tipo.slug];
            const nomeBase = `${selecionado.id}_0_${tipo.slug}`;
            const extensao = url.endsWith(".png") ? "png" : "jpg";
            return (
              <section key={tipo.slug} className="asset">
                <div className="previa">
                  {medida?.estado === "pronto" ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={medida.previa} alt={`${selecionado.name} ${tipo.rotulo}`} />
                  ) : (
                    <span className="vazio">
                      {medida?.estado === "erro" ? `erro: ${medida.motivo}` : "carregando…"}
                    </span>
                  )}
                </div>
                <div className="dados">
                  <strong>{tipo.rotulo}</strong>
                  {/* §A.4 item 7: formato e resolução antes do download */}
                  <span className="ficha">
                    {medida?.estado === "pronto"
                      ? `${medida.largura}×${medida.altura} · ${medida.mime} · ${bytesLegiveis(medida.blob.size)} · ddragon`
                      : "—"}
                  </span>
                  <div className="acoes">
                    <button
                      className="primario"
                      disabled={medida?.estado !== "pronto"}
                      onClick={() =>
                        medida?.estado === "pronto" &&
                        baixarBlob(medida.blob, `${nomeBase}.${extensao}`)
                      }
                    >
                      Baixar original (.{extensao})
                    </button>
                    <button
                      disabled={medida?.estado !== "pronto" || extensao === "png"}
                      onClick={() => medida && baixarComoPng(medida, nomeBase)}
                    >
                      {extensao === "png" ? "já é PNG" : "Baixar PNG"}
                    </button>
                    <button onClick={() => copiarUrl(url, tipo.slug)}>
                      {copiado === tipo.slug ? "copiado!" : "Copiar URL"}
                    </button>
                  </div>
                </div>
              </section>
            );
          })}
        </div>
      )}
    </main>
  );
}
