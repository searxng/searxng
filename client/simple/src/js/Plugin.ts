// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Base class for client-side plugins.
 *
 * @remarks
 * Handle conditional loading of the plugin in:
 *
 *   - client/simple/src/js/router.ts
 *
 * @abstract
 */
export abstract class Plugin {
  /**
   * Plugin name.
   */
  protected readonly id: string;

  /**
   * @remarks
   * Don't hold references of this instance outside the class.
   */
  protected constructor(id: string) {
    this.id = id;

    void this.invoke();
  }

  private async invoke(): Promise<void> {
    try {
      console.debug(`[PLUGIN] ${this.id}: Running...`);
      const result = await this.run();
      if (!result) return;

      console.debug(`[PLUGIN] ${this.id}: Running post-exec...`);
      // @ts-expect-error
      void (await this.post(result as NonNullable<Awaited<ReturnType<this["run"]>>>));
    } catch (error) {
      console.error(`[PLUGIN] ${this.id}:`, error);
    } finally {
      console.debug(`[PLUGIN] ${this.id}: Done.`);
    }
  }

  /**
   * Plugin goes here.
   *
   * @remarks
   * The plugin is already loaded at this point. If you wish to execute
   * conditions to exit early, consider moving the logic to:
   *
   *   - client/simple/src/js/router.ts
   *
   * ...to avoid unnecessarily loading this plugin on the client.
   */
  protected abstract run(): Promise<unknown>;

  /**
   * Post-execution hook.
   *
   * @remarks
   * The hook is only executed if `#run()` returns a truthy value.
   */
  // @ts-expect-error
  protected abstract post(result: NonNullable<Awaited<ReturnType<this["run"]>>>): Promise<void>;
}
