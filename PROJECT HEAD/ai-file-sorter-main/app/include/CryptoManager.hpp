#ifndef CRYPTOMANAGER_HPP
#define CRYPTOMANAGER_HPP

#include <string>
#include <vector>
#include <stdexcept>

class CryptoManager {
public:
    CryptoManager(const std::string &env_pc, const std::string &env_rr);
    std::string reconstruct();

private:
    static constexpr char embedded_pc[] = "insert-obfuscated-Key-part-1-here";
    std::string env_pc;
    std::string env_rr;
    std::string reassemble_key(const std::string &part1, const std::string &part2);
    std::string base64_decode(const std::string &encoded);
    std::string deobfuscate_with_salt(const std::string &obfuscated_data, const std::string &salt);
    std::string deobfuscate(const std::string &obfuscated_data);
    std::string aes256_decrypt(const std::vector<unsigned char> &ciphertext, const std::string &key);
};

#endif