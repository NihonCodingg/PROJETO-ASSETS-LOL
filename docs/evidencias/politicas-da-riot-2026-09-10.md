# Políticas da Riot — conferência de 10/09/2026

Registro da comparação do D6 (T-33). As páginas foram baixadas com `curl` em 10/09/2026, com o
User-Agent do projeto, e o texto foi extraído do HTML — sem passar por tradução, resumo ou
cópia de terceiros.

| Página | URL | Atualizada em | Onde está o aviso |
|---|---|---|---|
| General Policies | <https://developer.riotgames.com/policies/general> | 29/05/2025 | *Core Policies*, último item |
| Legal Jibber Jabber | <https://www.riotgames.com/en/legal> | agosto de 2018 | §6 |
| Documentação de LoL | <https://developer.riotgames.com/docs/lol> | — | *Legal Notices* — variante, não usada |

## Os textos, como estão no HTML

**General Policies**, dentro de `<p><em>…</em></p>`:

```text
[Your product] isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
```

**Legal Jibber Jabber**, com as entidades HTML preservadas:

```text
[The title of your Project] was created under Riot Games&#39; &quot;Legal Jibber Jabber&quot; policy using assets owned by Riot Games. &nbsp;Riot Games does not endorse or sponsor this project.
```

## Os bytes que importam

| Onde | No HTML | O que é | No site |
|---|---|---|---|
| `isn't`, `doesn't` | `'` | apóstrofo reto, `0x27` (conferido com `od -c`) | igual |
| `Riot Games'` | `&#39;` | apóstrofo reto, `0x27` | igual |
| `"Legal Jibber Jabber"` | `&quot;` | aspas retas, `0x22` | igual |
| depois de `Riot Games.` | `&nbsp;` | espaço não separável, somado a um espaço comum | um espaço comum |

O `&nbsp;` é a única diferença entre a página e o site, e é tipográfica: na tela ele vira dois
espaços entre as frases. O texto não muda.

## A variante que não foi usada

A seção *Legal Notices* da documentação de League of Legends repete o boilerplate com três
diferenças: sem contrações ("is not", "does not"), sem a vírgula depois de "Riot Games" e sem o
ponto final. O site segue a página de **políticas**: é ela a normativa, e é ela que tem data de
atualização.

## Quem mais faz assim

O Community Dragon — uma das duas fontes do site — publica o aviso do Legal Jibber Jabber no
rodapé do próprio site, e a documentação dele diz que o projeto foi reconhecido pela Riot pelo
Developer Portal. Nenhuma das páginas dele exige crédito formal; o site credita mesmo assim,
porque o §4 do Legal Jibber Jabber pede crédito a quem se aproveita do projeto de outro fã.
