{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11"; # (i) use /nixos-unstable to get latest packages, but maybe less caching
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default"; # (i) allows overriding systems easily, see https://github.com/nix-systems/nix-systems#consumer-usage
    devenv.url = "github:cachix/devenv";
  };

  outputs = { self, nixpkgs, nixpkgs-unstable, devenv, systems, flake-parts, ... } @ inputs: (
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = (import systems);
      imports = [
        inputs.devenv.flakeModule
      ];
      perSystem = { config, self', inputs', pkgs, system, ... }: # perSystem docs: https://flake.parts/module-arguments.html#persystem-module-parameters
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pkgs-latest = nixpkgs-unstable.legacyPackages.${system};
        in
        {
          devenv.shells.default = (import ./devenv.nix { inherit pkgs inputs pkgs-latest; });
        };
    }
  );

  nixConfig = {
    extra-substituters = [ "https://devenv.cachix.org" ];
    extra-trusted-public-keys = [ "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=" ];
  };
}
