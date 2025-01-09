{ pkgs ? import <nixpkgs> {} }:

/*
nix shell for development usage
1. run `nix-shell`
2. run `make run` (or any other make scripts)
Done!
*/

(pkgs.buildFHSEnv {
  name = "searxng";
  multiPkgs = pkgs: (with pkgs; [
    bash
    wget
    gnumake
    git
    python3
    geckodriver
    shellcheck
  ]);
  runScript = "bash";
}).env

