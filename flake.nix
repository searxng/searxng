{
  description = "SearXNG";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    pypi-deps-db = {
      url = "github:DavHau/pypi-deps-db";
      flake = false;
    };
    mach-nix-src.url = "github:DavHau/mach-nix";
    mach-nix-src.inputs.pypi-deps-db.follows = "pypi-deps-db";
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix-src, pypi-deps-db, ... }:
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

      # if updating python dependencies results in error
      #  "The given requirements might contain package versions which are not yet part of the dependency DB"
      # then
      # run `nix flake lock --update-input pypi-deps-db` to set lock file to most recent pypi-deps-db
      pypiDataRev = pypi-deps-db.rev;
      pypiDataSha256 = pypi-deps-db.narHash;
      # pypiDataSha256 = "1k66qyivkv6bhhpmddj2sw0i8mcq4fzrsnp6b3rlv7g5a0n1dbdf";
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
