# Docs: https://devenv.sh/basics/
{ pkgs, pkgs-latest, ... }: {

  languages = {
    # Docs: https://devenv.sh/languages/
    nix.enable = true;
  };

  packages = with pkgs; [
    # Search for packages: https://search.nixos.org/packages?channel=unstable&query=cowsay (note: this searches on unstable channel, your nixpkgs flake input might be on a release channel)
    hello
    pkgs-latest.hello
  ];

  pre-commit.hooks = {
    # Docs: https://devenv.sh/pre-commit-hooks/
    # list of pre-configured hooks: https://devenv.sh/reference/options/#pre-commithooks
    nil.enable = true; # nix check
    nixpkgs-fmt.enable = true; # nix formatting
  };

  difftastic.enable = true; # enable semantic diffs - https://devenv.sh/integrations/difftastic/
}
