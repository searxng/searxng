import { listen } from "./toolkit.ts";

listen("click", ".close", function (this: HTMLElement) {
  (this.parentNode as HTMLElement)?.classList.add("invisible");
});
