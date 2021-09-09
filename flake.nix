{
  description = "SearXNG";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    mach-nix-src.url = "github:DavHau/mach-nix";
    flake-utils.url = "github:numtide/flake-utils";
  };

  inputs.flake-compat = {
    url = "github:edolstra/flake-compat";
    flake = false;
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix-src, ... }:
    let
      # TODO : for some reason `nix flake show` results in error:
      # ```error: a 'aarch64-darwin' with features {} is required to build '/nix/store/s79ixgs3xy250x1b9vyy90g7dzd6bsh4-conda-channels.json.drv',
      #   but I am a 'x86_64-linux' with features {benchmark, big-parallel, kvm, nixos-test}```
      # Some internal part of mach-nix attempts to build derivation into target system and cross-build fails
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      #
      # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
      forAllSystems = f:
        nixpkgs.lib.genAttrs supportedSystems (system: f system);

      python = "python38";
      pypiDataRev = "18250538b9eeb9484c4e3bdf135bc1f3a2ccd949";
      pypiDataSha256 = "01hdjy5rpcjm92fyp8n6lci773rgbsa81h2n08r49zjhk9michrb";
      requirements = builtins.readFile ./requirements.txt;

      nixpkgsFor = forAllSystems (
        system:
          import nixpkgs {
            inherit system;
            overlays = [ self.overlay ];
          }
      );
    in
      {

        overlay = final: prev:
          let
            mach-nix = import mach-nix-src {
              pkgs = prev;
              inherit python pypiDataRev pypiDataSha256;
            };
          in
            {
              searxng = (
                mach-nix.buildPythonPackage {
                  inherit requirements;
                  pname = "SearXNG";
                  version = "1.0";
                  src = ./.;
                }
              );
              dev-python =
                  mach-nix.mkPython {
                    inherit python;
                    requirements = requirements;
                  };
            };
        packages = forAllSystems (
          system:
            {
              inherit (nixpkgsFor.${system}) searxng;
            }
        );

        # The default package for 'nix build'. This makes sense if the
        # flake provides only one package or there is a clear "main"
        # package.
        # Returns Searx with plugin enabled
        defaultPackage = forAllSystems (system: self.packages.${system}.searxng);

        # To use as `nix develop`
        # will provide shell with
        # - make utility for `make run` and `make test`
        # - python with dependencies, to run searx built with nix
        # - env var pointing to default repository searx config
        devShell = forAllSystems (
          system: nixpkgsFor.${system}.mkShell
            rec {
              buildInputs = with nixpkgsFor.${system}; [
                dev-python
                gnumake
              ];
              settingsFile = builtins.readFile ./searx/settings.yml;
              SEARX_SETTINGS_PATH = "${settingsFile}";
            }
        );

        nixosModules.searxng = { pkgs, ... }:
          {
            nixpkgs.overlays = [ self.overlay ];
          };
      };
}
