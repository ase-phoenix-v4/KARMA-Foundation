// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract KARMALivingNFT {
    struct LivingNFT {
        uint256 id;
        uint8 level;
        uint256 birthTime;
        uint256 karmaBalance;
        uint256 parentId;
        uint256 generation;
        bool isActive;
        uint256 str;
        uint256 rar;
        uint256 erg;
    }

    mapping(uint256 => LivingNFT) public nfts;
    mapping(address => uint256[]) public ownerNFTs;
    uint256 public nftCounter;
    address public immutable ARCHITECT;

    event NFTMinted(address indexed owner, uint256 indexed nftId, uint8 level, uint256 generation);
    event NFTDivided(uint256 indexed parentId, uint256 indexed child1, uint256 indexed child2);
    event NFTPhoenixBurn(uint256 indexed nft1, uint256 indexed nft2, uint256 indexed newNftId, uint8 newLevel);
    event KARMAAccumulated(uint256 indexed nftId, uint256 amount);

    constructor() {
        ARCHITECT = msg.sender;
        _mintNFT(ARCHITECT, 5, 0, 1, 100, 100, 100);
    }

    function mintNFT() external {
        require(nftCounter < 10000, "Max supply reached");
        _mintNFT(msg.sender, 1, 0, 1, 50, 50, 50);
    }
