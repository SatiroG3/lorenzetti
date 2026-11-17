#include "CaloCell/CaloDetDescriptor.h"

#include <cassert>
#include <iostream>

int main()
{
    using namespace xAOD;

    CaloDetDescriptor descriptor(
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

    std::cout << "Energia inicial: " << descriptor.e() << '\n';
    std::cout << "Tau inicial: " << descriptor.tau() << '\n';
    std::cout << "Sigma inicial: " << descriptor.sigma() << '\n';

    assert(descriptor.e() == 0.0f);
    assert(descriptor.tau() == 0.0f);
    assert(descriptor.sigma() == 0.0f);

    std::cout << "TESTE APROVADO: atributos inicializados corretamente.\n";

    return 0;
}
