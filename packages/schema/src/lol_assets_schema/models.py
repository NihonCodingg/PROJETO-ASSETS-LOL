"""Modelos Pydantic do contrato do índice.

O JSON Schema em `schemas/` continua sendo a fonte de verdade; estes modelos são
a forma de o indexador e a API manipularem o contrato sem dicionário solto. Um
teste de paridade garante que os dois não divirjam.

Os campos são `snake_case` em Python e saem em `camelCase` no JSON, que é o que o
schema declara. Sempre serialize com `model_dump(by_alias=True, exclude_none=True)`.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

AssetCategory = Literal[
    "champion",
    "item",
    "profile_icon",
    "rune",
    "summoner_spell",
    "emote",
    "ward",
    "map",
    "rank",
    "misc",
]

#: Nomes canônicos do ADR 0002. Os nomes das fontes ("centered", "uncentered")
#: são proibidos aqui de propósito: as duas fontes os usam trocados.
AssetType = Literal[
    "square",
    "splash_centered",
    "splash_wide",
    "loading",
    "loading_vintage",
    "tile",
    "chroma",
    "ability_icon",
    "passive_icon",
    "item_icon",
    "profile_icon",
    "rune_icon",
    "rune_tree_icon",
    "stat_mod_icon",
    "summoner_spell_icon",
    "emote_icon",
    "ward_icon",
    "map_image",
    "rank_emblem",
]

AssetSource = Literal["ddragon", "cdragon", "riot_static", "wiki"]

#: Tipos que só existem por skin — ADR 0002.
SKIN_SCOPED_TYPES = frozenset(
    {"splash_centered", "splash_wide", "loading", "loading_vintage", "tile", "chroma"}
)

Version = Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$")]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def _to_camel(name: str) -> str:
    first, *rest = name.split("_")
    return first + "".join(part.title() for part in rest)


class _Base(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class LocalizedName(BaseModel):
    """As chaves são os códigos de idioma, então aqui não há camelCase a gerar."""

    model_config = ConfigDict(extra="forbid")

    pt_BR: str = Field(min_length=1)
    en_US: str | None = Field(default=None, min_length=1)


class Asset(_Base):
    id: Annotated[str, Field(pattern=r"^[a-z_]+:[A-Za-z0-9_.-]+$")]
    type: AssetType
    category: AssetCategory

    champion_key: int | None = Field(default=None, ge=1)
    champion_id: str | None = None
    skin_id: int | None = Field(default=None, ge=1)
    skin_num: int | None = Field(default=None, ge=0)
    is_base_skin: bool | None = None
    parent_skin_num: int | None = Field(default=None, ge=0)
    item_id: int | None = Field(default=None, ge=1)
    ref_id: str | None = None

    names: LocalizedName
    aliases: list[str] | None = None
    tags: list[str] | None = None

    source: AssetSource
    source_url: str
    #: Ausente em versões sem assets copiados: aí o front usa `source_url` (ADR 0007).
    storage_key: str | None = None
    file_name: Annotated[str, Field(pattern=r"^[A-Za-z0-9_.-]+\.(png|jpg)$")]

    width: int = Field(ge=1)
    height: int = Field(ge=1)
    format: Literal["png", "jpeg"]
    has_alpha: bool
    bytes: int = Field(ge=1)
    sha256: Sha256

    @model_validator(mode="after")
    def _regras_dos_adrs(self) -> Self:
        if self.has_alpha and self.format != "png":
            raise ValueError(
                "ADR 0001 regra 4: asset com canal alfa nunca pode ser JPEG "
                f"(id={self.id}, format={self.format})"
            )
        if self.category == "champion" and (self.champion_key is None or self.champion_id is None):
            raise ValueError(f"asset de campeão exige championKey e championId (id={self.id})")
        if self.type in SKIN_SCOPED_TYPES and (self.skin_id is None or self.skin_num is None):
            raise ValueError(
                f"ADR 0002: corte por skin exige skinId e skinNum (id={self.id}, type={self.type})"
            )
        return self


class IndexShard(_Base):
    """Uma fatia de assets. Carregada sob demanda, não na abertura (ADR 0010)."""

    schema_version: Version
    game_version: Version
    category: AssetCategory
    generated_at: str
    assets_base_url: str | None = None
    assets: list[Asset]


class CatalogChampion(_Base):
    """Nível de navegação: a grade padrão."""

    champion_key: int = Field(ge=1)
    champion_id: str
    names: LocalizedName
    title: LocalizedName | None = None
    tags: list[str] | None = None
    aliases: list[str] | None = None
    #: Exibido no cartão. Conta skins, não chromas.
    skin_count: int = Field(ge=1)
    chroma_count: int | None = Field(default=None, ge=0)
    base_skin_id: int = Field(ge=1)
    thumbnail_key: str | None = None
    thumbnail_url: str | None = None


class CatalogSkin(_Base):
    """Nível de busca. `champion_key` é obrigatório: é o rótulo do resultado."""

    skin_id: int = Field(ge=1)
    skin_num: int = Field(ge=0)
    champion_key: int = Field(ge=1)
    names: LocalizedName
    is_base: bool
    chroma_count: int | None = Field(default=None, ge=0)
    thumbnail_key: str | None = None
    thumbnail_url: str | None = None


class Catalog(_Base):
    """As duas projeções do ADR 0010, e nenhum asset."""

    schema_version: Version
    game_version: Version
    generated_at: str
    assets_base_url: str | None = None
    champions: list[CatalogChampion]
    skins: list[CatalogSkin]


class CatalogRef(_Base):
    url: str
    champions: int = Field(ge=0)
    skins: int = Field(ge=0)
    bytes: int = Field(ge=0)
    sha256: Sha256 | None = None


class ShardRef(_Base):
    category: str
    url: str
    assets: int = Field(ge=0)
    bytes: int = Field(ge=0)
    sha256: Sha256 | None = None


class ZipRef(_Base):
    category: str
    url: str
    bytes: int = Field(ge=0)
    assets: int | None = Field(default=None, ge=0)
    sha256: Sha256 | None = None


class ManifestVersion(_Base):
    game_version: Version
    indexed_at: str
    #: `False` = só índice; o front usa `source_url` de cada asset (ADR 0007).
    assets_copied: bool
    catalog: CatalogRef
    total_assets: int | None = Field(default=None, ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    shards: list[ShardRef] = Field(min_length=1)
    zips: list[ZipRef] | None = None


class Generation(_Base):
    """Assinatura de geração: o que o indexador **produziria diferente** hoje (T-38).

    Existe porque a decisão de reindexar comparava só a versão do jogo, e a Riot
    publica patch a cada duas semanas. Uma melhoria no indexador — etiquetas de
    filtro, uma categoria nova — ficava até quinze dias sem chegar ao site, sem
    ninguém perceber que o índice publicado estava velho **de código** enquanto
    parecia novo de versão.

    Deliberadamente **não** é hash do código-fonte: isso reindexaria 2,39 GB a
    cada refatoração e a cada bump de dependência. São dois campos, e os dois
    mudam só quando a saída muda de verdade.
    """

    #: Sobe à mão quando um construtor passa a produzir registro diferente.
    indexer: int = Field(ge=1)
    #: As categorias que esta execução emite. Categoria nova muda a assinatura.
    categories: list[str] = Field(min_length=1)


class IndexManifest(_Base):
    """O único arquivo de nome fixo no bucket."""

    schema_version: Version
    generated_at: str
    assets_base_url: str | None = None
    current_version: Version
    #: Ausente nos índices gerados antes do T-38 — e ausente significa reindexar.
    generation: Generation | None = None
    versions: list[ManifestVersion] = Field(min_length=1)


# --- status da execução (T-12) -------------------------------------------------
#
# Não faz parte do contrato que o front precisa para funcionar: é o relatório da
# última indexação, escrito com sucesso ou com falha. Como não há processo
# monitorando nada (§11 da Spec), ele e a issue automática são o canal inteiro.


class StatusFailure(_Base):
    #: Nome da classe da exceção — agrupa falhas repetidas sem depender do texto.
    kind: str = Field(min_length=1)
    message: str


class StatusCounts(_Base):
    assets: int | None = Field(default=None, ge=0)
    champions: int | None = Field(default=None, ge=0)
    skins: int | None = Field(default=None, ge=0)
    categories: int | None = Field(default=None, ge=0)
    assets_by_category: dict[str, int] | None = None
    assets_by_source: dict[str, int] | None = None


class StatusBytes(_Base):
    index: int | None = Field(default=None, ge=0)
    catalog_gzip: int | None = Field(default=None, ge=0)
    largest_shard_gzip: int | None = Field(default=None, ge=0)
    #: Soma dos bytes que o índice descreve. Nada disso é copiado (ADR 0012).
    described_assets: int | None = Field(default=None, ge=0)


class StatusSource(_Base):
    files: int | None = Field(default=None, ge=0)
    images_measured: int | None = Field(default=None, ge=0)
    images_skipped: int | None = Field(default=None, ge=0)
    unreadable: dict[str, int] | None = None
    case_mismatches: int | None = Field(default=None, ge=0)


class StatusMerge(_Base):
    """O que a fusão de fontes fez (T-17)."""

    winners_by_source: dict[str, int] | None = None
    losers_by_source: dict[str, int] | None = None
    exclusive_by_source: dict[str, int] | None = None
    ties: int | None = Field(default=None, ge=0)
    #: O S2 mediu empate em tudo. Passar de zero significa que a premissa mudou.
    resolution_wins: int | None = Field(default=None, ge=0)


class DimensionDeviation(_Base):
    """Um tipo cujo tamanho fugiu do que os spikes mediram."""

    type: AssetType
    expected: tuple[int, int]
    found: tuple[int, int]
    assets: int = Field(ge=1)
    example: str | None = None


class IndexStatus(_Base):
    schema_version: Version
    started_at: str
    finished_at: str
    duration_seconds: float = Field(ge=0)
    ok: bool
    game_version: Version | None = None
    #: `GITHUB_RUN_ID` — chave de idempotência da issue automática.
    run_id: str | None = None
    failure: StatusFailure | None = None
    counts: StatusCounts | None = None
    bytes: StatusBytes | None = None
    source: StatusSource | None = None
    merge: StatusMerge | None = None
    unexpected_dimensions: list[DimensionDeviation] | None = None
