module IESoptAddon_BatterySoftMin

using IESopt
import JuMP

function initialize!(model::JuMP.Model, config::Dict)
    return true
end

function construct_objective!(model::JuMP.Model, config::Dict)
    T = get_T(model)
    w = [internal(model).model.snapshots[t].weight for t in T]
    battery = get_component(model, "bromberg.battery_storage")

    soc_min = config["soc_min"]
    total_capacity = config["total_capacity"]
    penalty = config["penalty"]

    battery.var.softmin = JuMP.@variable(
        model,
        [t = T],
        lower_bound = 0,
        container = Array
    )

    battery.con.softmin = JuMP.@constraint(
        model,
        [t = T],
        battery.var.state[t] >= (total_capacity * soc_min) - battery.var.softmin[t],
        container = Array
    )

    battery.obj.softmin = sum(battery.var.softmin[t] * w[t] * penalty for t in T)
    push!(internal(model).model.objectives["total_cost"].terms, battery.obj.softmin)

    return true
end

end
