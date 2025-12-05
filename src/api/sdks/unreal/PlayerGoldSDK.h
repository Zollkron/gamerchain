/*
 * PlayerGold SDK para Unreal Engine
 * Header file para integración de blockchain PlayerGold en juegos Unreal
 */

#pragma once

#include "CoreMinimal.h"
#include "Http.h"
#include "Json.h"
#include "JsonUtilities.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "PlayerGoldSDK.generated.h"

// Delegates para callbacks
DECLARE_DYNAMIC_DELEGATE_OneParam(FOnBalanceReceived, float, Balance);
DECLARE_DYNAMIC_DELEGATE_OneParam(FOnTransactionCreated, FString, TransactionHash);
DECLARE_DYNAMIC_DELEGATE_OneParam(FOnError, FString, ErrorMessage);

// Estructuras de datos
USTRUCT(BlueprintType)
struct FPlayerGoldBalance
{
    GENERATED_BODY()
    
    UPROPERTY(BlueprintReadOnly)
    FString Address;
    
    UPROPERTY(BlueprintReadOnly)
    float Balance;
    
    UPROPERTY(BlueprintReadOnly)
    FString Timestamp;
};

USTRUCT(BlueprintType)
struct FPlayerGoldTransaction
{
    GENERATED_BODY()
    
    UPROPERTY(BlueprintReadOnly)
    FString FromAddress;
    
    UPROPERTY(BlueprintReadOnly)
    FString ToAddress;
    
    UPROPERTY(BlueprintReadOnly)
    float Amount;
    
    UPROPERTY(BlueprintReadOnly)
    float Fee;
    
    UPROPERTY(BlueprintReadOnly)
    FString Status;
    
    UPROPERTY(BlueprintReadOnly)
    int32 Confirmations;
};

USTRUCT(BlueprintType)
struct FPlayerGoldNetworkStatus
{
    GENERATED_BODY()
    
    UPROPERTY(BlueprintReadOnly)
    int32 ChainLength;
    
    UPROPERTY(BlueprintReadOnly)
    int32 LastBlockIndex;
    
    UPROPERTY(BlueprintReadOnly)
    FString LastBlockHash;
    
    UPROPERTY(BlueprintReadOnly)
    int32 PendingTransactions;
    
    UPROPERTY(BlueprintReadOnly)
    int32 Difficulty;
};

/**
 * Subsistema principal del SDK de PlayerGold para Unreal Engine
 */
UCLASS()
class PLAYERGOLD_API UPlayerGoldSDK : public UGameInstanceSubsystem
{
    GENERATED_BODY()
    
public:
    // Inicialización
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;
    
    /**
     * Inicializa el SDK con la API key
     * @param InApiKey - API key del desarrollador
     * @param InApiUrl - URL base de la API (opcional)
     */
    UFUNCTION(BlueprintCallable, Category = "PlayerGold")
    void InitializeSDK(const FString& InApiKey, const FString& InApiUrl = TEXT("http://localhost:5000/api/v1"));
    
    /**
     * Obtiene el saldo de una dirección
     * @param Address - Dirección de la wallet
     * @param OnSuccess - Callback cuando se obtiene el saldo exitosamente
     * @param OnError - Callback cuando hay un error
     */
    UFUNCTION(BlueprintCallable, Category = "PlayerGold")
    void GetBalance(const FString& Address, FOnBalanceReceived OnSuccess, FOnError OnError);
    
    /**
     * Crea una nueva transacción
     * @param FromAddress - Dirección origen
     * @param ToAddress - Dirección destino
     * @param Amount - Cantidad a transferir
     * @param PrivateKey - Clave privada para firmar
     * @param OnSuccess - Callback cuando se crea la transacción
     * @param OnError - Callback cuando hay un error
     */
    UFUNCTION(BlueprintCallable, Category = "PlayerGold")
    void CreateTransaction(
        const FString& FromAddress,
        const FString& ToAddress,
        float Amount,
        const FString& PrivateKey,
        FOnTransactionCreated OnSuccess,
        FOnError OnError
    );
    
    /**
     * Obtiene información de una transacción
     * @param TransactionHash - Hash de la transacción
     */
    UFUNCTION(BlueprintCallable, Category = "PlayerGold")
    void GetTransaction(const FString& TransactionHash);
    
    /**
     * Obtiene el estado de la red
     */
    UFUNCTION(BlueprintCallable, Category = "PlayerGold")
    void GetNetworkStatus();
    
    /**
     * Verifica si el SDK está autenticado
     */
    UFUNCTION(BlueprintPure, Category = "PlayerGold")
    bool IsAuthenticated() const { return !AuthToken.IsEmpty(); }
    
private:
    // Configuración
    FString ApiUrl;
    FString ApiKey;
    FString AuthToken;
    double TokenExpirationTime;
    
    // HTTP Module
    FHttpModule* HttpModule;
    
    // Métodos privados
    void Authenticate();
    void OnAuthenticationResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    void OnBalanceResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FOnBalanceReceived OnSuccess, FOnError OnError);
    void OnTransactionResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FOnTransactionCreated OnSuccess, FOnError OnError);
    
    TSharedRef<IHttpRequest> CreateRequest(const FString& Endpoint, const FString& Verb = TEXT("GET"));
    void EnsureAuthenticated();
};
