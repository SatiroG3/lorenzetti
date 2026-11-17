#include "CaloCell/CaloDetDescriptor.h"

#include <iostream>
#include <memory>

int main()
{
    using namespace xAOD;

    CaloDetDescriptor original(
        0.0f,
        0.0f,
        0.1f,
        0.1f,
        1UL,
        0.0f,
        static_cast<CaloSampling>(0),
        static_cast<Detector>(0),
        25.0f,
        0,
        0,
        false
    );

    // Valores conhecidos para o teste
    original.setE(1000.0f);
    original.setTau(25.0f);
    original.setSigma(90.0f);

    // Executa o metodo investigado
    std::unique_ptr<CaloDetDescriptor> copia(original.copy());

    if (!copia) {
        std::cerr << "ERRO: copy() retornou nullptr.\n";
        return 1;
    }

    std::cout << "================================\n";
    std::cout << "TESTE DE COPIA DO DESCRIPTOR\n";
    std::cout << "================================\n";

    std::cout << "Energia: "
              << original.e() << " -> " << copia->e() << '\n';

    std::cout << "Tau: "
              << original.tau() << " -> " << copia->tau() << '\n';

    std::cout << "Sigma: "
              << original.sigma() << " -> " << copia->sigma() << '\n';

    bool energia_ok = (original.e() == copia->e());
    bool tau_ok = (original.tau() == copia->tau());
    bool sigma_ok = (original.sigma() == copia->sigma());

    std::cout << "\nRESULTADOS:\n";
    std::cout << "Energia: " << (energia_ok ? "OK" : "FALHOU") << '\n';
    std::cout << "Tau: " << (tau_ok ? "OK" : "FALHOU") << '\n';
    std::cout << "Sigma: " << (sigma_ok ? "OK" : "FALHOU") << '\n';

    if (!energia_ok || !tau_ok || !sigma_ok) {
        std::cerr << "\nTESTE REPROVADO: copia inconsistente.\n";
        return 1;
    }

    std::cout << "\nTESTE APROVADO: atributos preservados.\n";

    return 0;
}
