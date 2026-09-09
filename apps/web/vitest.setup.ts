/**
 * O mínimo que o jsdom não traz e os componentes precisam.
 *
 * `ResizeObserver` é usado pelo cmdk e pelo TanStack Virtual. Sem ele, todo
 * teste de componente que renderize a paleta morre com `ReferenceError` — e o
 * erro não tem nada a ver com o que o teste queria provar.
 *
 * O stub não mede nada de propósito: jsdom não faz layout, então qualquer
 * medida seria ficção. Os testes que dependem de tamanho verificam **que a
 * virtualização está ativa**, não quantos pixels ela calculou.
 */
class ResizeObserverStub implements ResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

globalThis.ResizeObserver ??= ResizeObserverStub;

// O jsdom não implementa `scrollIntoView`, que o cmdk chama ao mover a seleção.
Element.prototype.scrollIntoView ??= function scrollIntoView(): void {};
